import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from app.schemas.artifact import ArtifactCreate, ArtifactRead
from app.services.detection_service import DetectionService

logger = logging.getLogger(__name__)


class ArtifactService:
    """
    Forensic artifact ingestion and querying service.
    Coordinates evidence persistence and triggers post-ingestion adversary detection.
    """

    _instance: Optional["ArtifactService"] = None

    def __init__(self, detection_service: Optional[DetectionService] = None):
        self.detection_service = detection_service or DetectionService.get_instance()
        self._artifacts: Dict[str, ArtifactRead] = {}

    @classmethod
    def get_instance(cls) -> "ArtifactService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def clear(self) -> None:
        """Clear state for isolated test runs."""
        self._artifacts.clear()

    async def ingest_artifacts(
        self,
        artifacts: Union[ArtifactCreate, List[ArtifactCreate], Dict[str, Any], List[Dict[str, Any]]],
        job_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plan: Optional[Dict[str, Any]] = None,
    ) -> List[ArtifactRead]:
        """
        Persists newly submitted forensic artifacts, then evaluates detection rules.
        Detection engine failure is non-fatal to ensure evidentiary integrity.
        """
        if not isinstance(artifacts, list):
            items = [artifacts]
        else:
            items = artifacts

        persisted: List[ArtifactRead] = []
        now = datetime.now(timezone.utc)

        for item in items:
            if isinstance(item, dict):
                art_id = item.get("id") or f"art-{uuid.uuid4().hex[:12]}"
                art_job_id = item.get("job_id") or job_id or "unknown-job"
                art_agent_id = item.get("agent_id") or agent_id or "unknown-agent"
                art_type = item.get("type", "unknown")
                art_data = item.get("data", {})
                collected_at = item.get("collected_at") or now
            else:
                art_id = getattr(item, "id", None) or f"art-{uuid.uuid4().hex[:12]}"
                art_job_id = getattr(item, "job_id", None) or job_id or "unknown-job"
                art_agent_id = getattr(item, "agent_id", None) or agent_id or "unknown-agent"
                art_type = getattr(item, "type", "unknown")
                art_data = getattr(item, "data", {})
                collected_at = getattr(item, "collected_at", None) or now

            if isinstance(collected_at, str):
                try:
                    collected_at = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
                except Exception:
                    collected_at = now

            record = ArtifactRead(
                id=art_id,
                job_id=art_job_id,
                agent_id=art_agent_id,
                type=art_type,
                data=art_data,
                collected_at=collected_at,
            )
            self._artifacts[art_id] = record
            persisted.append(record)

        # 2. Trigger Detection Engine (guarded against failures)
        new_detections = []
        try:
            new_detections = await self.detection_service.process_artifacts(
                artifacts=persisted,
                job_id=job_id,
                agent_id=agent_id,
                plan=plan,
            )
        except Exception as e:
            # Preservation guarantee: detection failure must NOT corrupt or roll back ingested artifacts
            logger.error(f"Detection engine error during artifact ingestion: {e}", exc_info=True)

        # 3. Broadcast Live Events to Connected WebSocket Clients
        try:
            from app.api.websocket.jobs import manager as ws_manager
            from app.services.job_service import JobService

            for record in persisted:
                target_job = record.job_id if record.job_id != "unknown-job" else job_id
                if target_job and target_job != "unknown-job":
                    await ws_manager.broadcast_job_event(target_job, {
                        "event": "artifact_collected",
                        "job_id": target_job,
                        "agent_id": record.agent_id,
                        "timestamp": record.collected_at.isoformat(),
                        "payload": {
                            "id": record.id,
                            "type": record.type,
                            "data": record.data,
                        },
                    })

            if new_detections:
                for det in new_detections:
                    target_job = det.job_id if det.job_id != "unknown-job" else job_id
                    if target_job and target_job != "unknown-job":
                        await ws_manager.broadcast_job_event(target_job, {
                            "event": "threat_detected",
                            "job_id": target_job,
                            "detection": det.model_dump(mode="json"),
                        })

            if job_id and job_id != "unknown-job":
                await JobService.get_instance().update_job_status(job_id, "completed")
                await ws_manager.broadcast_job_event(job_id, {
                    "event": "job_status",
                    "job_id": job_id,
                    "status": "completed",
                    "timestamp": now.isoformat(),
                })
        except Exception as ws_err:
            logger.debug(f"Live job event broadcast notice: {ws_err}")

        return persisted


    async def list_artifacts(
        self,
        job_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        type_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ArtifactRead]:
        """Query stored forensic artifacts with optional filtering."""
        results = list(self._artifacts.values())

        if job_id:
            results = [a for a in results if a.job_id == job_id]
        if agent_id:
            results = [a for a in results if a.agent_id == agent_id]
        if type_filter:
            results = [a for a in results if a.type.lower() == type_filter.lower()]

        results.sort(key=lambda a: a.collected_at, reverse=True)
        return results[offset : offset + limit]

    async def get_artifact(self, artifact_id: str) -> Optional[ArtifactRead]:
        """Retrieve a specific forensic artifact by ID."""
        return self._artifacts.get(artifact_id)
