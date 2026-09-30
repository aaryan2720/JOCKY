import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.detection.engine import DetectionEngine
from app.models.detection import DetectionModel
from app.schemas.detection import DetectionCreate, DetectionRead, EvidenceReference

logger = logging.getLogger(__name__)


class DetectionService:
    """
    Business logic and management service for threat detections backed by PostgreSQL / SQLAlchemy.
    Coordinates artifact evaluation with DetectionEngine, deterministic deduplication, and database persistence.
    """

    _instance: Optional["DetectionService"] = None

    def __init__(self, engine: Optional[DetectionEngine] = None, session_factory=AsyncSessionLocal):
        self.engine = engine or DetectionEngine()
        self._session_factory = session_factory

    @classmethod
    def get_instance(cls) -> "DetectionService":
        """Singleton accessor for service state."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_state(cls) -> None:
        """Clear state for isolated test execution."""
        cls._instance = None

    def clear(self) -> None:
        """Clear singleton state for test harnesses."""
        pass

    async def process_artifacts(
        self,
        artifacts: List[Any],
        job_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plan: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionRead]:
        """
        Evaluates artifacts against detection rules, applies persistent deduplication,
        and saves newly created detections into the PostgreSQL database.
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
        if not raw_detections:
            return persisted

        async with self._session_factory() as session:
            for det_create, dedup_key in raw_detections:
                # Persistent deduplication check
                if dedup_key:
                    existing_stmt = select(DetectionModel).where(DetectionModel.dedup_key == dedup_key)
                    existing_res = await session.execute(existing_stmt)
                    if existing_res.scalar_one_or_none():
                        logger.debug(f"Skipping duplicate detection with key: {dedup_key}")
                        continue

                det_id = f"det-{uuid.uuid4().hex[:12]}"
                now = datetime.now(timezone.utc)

                evidence_data = []
                for ev in det_create.evidence:
                    if hasattr(ev, "model_dump"):
                        evidence_data.append(ev.model_dump(mode="json"))
                    elif isinstance(ev, dict):
                        evidence_data.append(ev)
                    else:
                        evidence_data.append({"raw": str(ev)})

                det_model = DetectionModel(
                    id=det_id,
                    agent_id=det_create.agent_id or agent_id or "unknown",
                    job_id=det_create.job_id or job_id,
                    severity=det_create.severity,
                    title=det_create.title,
                    description=det_create.description,
                    rule_id=det_create.rule_id,
                    status=det_create.status,
                    evidence=evidence_data,
                    dedup_key=dedup_key,
                    created_at=now,
                )
                session.add(det_model)
                await session.flush()

                persisted.append(
                    DetectionRead(
                        id=det_id,
                        agent_id=det_model.agent_id,
                        job_id=det_model.job_id,
                        severity=det_model.severity,
                        title=det_model.title,
                        description=det_model.description,
                        rule_id=det_model.rule_id,
                        status=det_model.status,
                        evidence=[EvidenceReference.model_validate(e) for e in evidence_data],
                        created_at=now,
                    )
                )

            await session.commit()

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
        """Query stored detections from database with filtering."""
        async with self._session_factory() as session:
            stmt = select(DetectionModel)

            if agent_id:
                stmt = stmt.where(DetectionModel.agent_id == agent_id)
            if job_id:
                stmt = stmt.where(DetectionModel.job_id == job_id)
            if severity:
                stmt = stmt.where(func.lower(DetectionModel.severity) == severity.lower())
            if status:
                stmt = stmt.where(func.lower(DetectionModel.status) == status.lower())
            if rule_id:
                stmt = stmt.where(func.lower(DetectionModel.rule_id) == rule_id.lower())

            stmt = stmt.order_by(DetectionModel.created_at.desc()).offset(offset).limit(limit)
            res = await session.execute(stmt)
            detections = res.scalars().all()

            results = []
            for d in detections:
                results.append(
                    DetectionRead(
                        id=d.id,
                        agent_id=d.agent_id,
                        job_id=d.job_id,
                        severity=d.severity,
                        title=d.title,
                        description=d.description,
                        rule_id=d.rule_id,
                        status=d.status,
                        evidence=[EvidenceReference.model_validate(e) for e in (d.evidence or [])],
                        created_at=d.created_at,
                    )
                )
            return results

    async def get_detection(self, detection_id: str) -> Optional[DetectionRead]:
        """Fetch single detection by ID from database."""
        async with self._session_factory() as session:
            d = await session.get(DetectionModel, detection_id)
            if d:
                return DetectionRead(
                    id=d.id,
                    agent_id=d.agent_id,
                    job_id=d.job_id,
                    severity=d.severity,
                    title=d.title,
                    description=d.description,
                    rule_id=d.rule_id,
                    status=d.status,
                    evidence=[EvidenceReference.model_validate(e) for e in (d.evidence or [])],
                    created_at=d.created_at,
                )
            return None
