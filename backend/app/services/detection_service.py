import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.detection.engine import DetectionEngine, compute_dedup_key
from app.schemas.detection import (
    DetectionCreate,
    DetectionRead,
    EvidenceReference,
)

logger = logging.getLogger(__name__)


class DetectionService:
    """
    Business logic and management service for threat detections.
    Coordinates artifact evaluation with DetectionEngine, deduplication, and persistence.
    """

    _instance: Optional["DetectionService"] = None

    def __init__(self, engine: Optional[DetectionEngine] = None):
        self.engine = engine or DetectionEngine()
        # In-memory storage for deterministic speed and testing
        self._detections: Dict[str, DetectionRead] = {}
        self._dedup_keys: set[str] = set()

    @classmethod
    def get_instance(cls) -> "DetectionService":
        """Singleton accessor for in-process service state."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def clear(self) -> None:
        """Clear state for isolated test execution."""
        self._detections.clear()
        self._dedup_keys.clear()

    async def process_artifacts(
        self,
        artifacts: List[Any],
        job_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plan: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionRead]:
        """
        Evaluates artifacts, applies deduplication, and persists new detections.
        """
        if not artifacts:
            return []

        # Run detection engine
        raw_detections = self.engine.evaluate_artifacts(
            artifacts=artifacts,
            plan=plan,
            context=context,
        )

        persisted: List[DetectionRead] = []

        for det_create, dedup_key in raw_detections:
            # Deduplication check
            if dedup_key in self._dedup_keys:
                logger.debug(f"Skipping duplicate detection with key: {dedup_key}")
                continue

            self._dedup_keys.add(dedup_key)
            det_id = f"det-{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)

            det_read = DetectionRead(
                id=det_id,
                agent_id=det_create.agent_id or agent_id or "unknown",
                job_id=det_create.job_id or job_id,
                severity=det_create.severity,
                title=det_create.title,
                description=det_create.description,
                rule_id=det_create.rule_id,
                status=det_create.status,
                evidence=det_create.evidence,
                created_at=now,
            )

            self._detections[det_id] = det_read
            persisted.append(det_read)

        return persisted

    async def list_detections(
        self,
        agent_id: Optional[str] = None,
        job_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        rule_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DetectionRead]:
        """Query stored detections with filtering."""
        results = list(self._detections.values())

        if agent_id:
            results = [d for d in results if d.agent_id == agent_id]
        if job_id:
            results = [d for d in results if d.job_id == job_id]
        if severity:
            results = [d for d in results if d.severity.lower() == severity.lower()]
        if status:
            results = [d for d in results if d.status.lower() == status.lower()]
        if rule_id:
            results = [d for d in results if d.rule_id.lower() == rule_id.lower()]

        # Sort by creation timestamp descending
        results.sort(key=lambda d: d.created_at, reverse=True)

        return results[offset : offset + limit]

    async def get_detection(self, detection_id: str) -> Optional[DetectionRead]:
        """Fetch single detection by ID."""
        return self._detections.get(detection_id)
