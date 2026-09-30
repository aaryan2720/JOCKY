import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.artifact import ArtifactModel
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactItem,
    ArtifactListResponse,
    ArtifactRead,
    ArtifactSubmissionRequest,
    ArtifactSubmissionResponse,
)
from app.services.detection_service import DetectionService

logger = logging.getLogger(__name__)


class ArtifactService:
    """
    Forensic artifact ingestion and querying service backed by PostgreSQL / SQLAlchemy.
    Coordinates evidence persistence, batch ingestion, and triggers post-ingestion adversary detection.
    """

    _instance: Optional["ArtifactService"] = None

    def __init__(self, detection_service: Optional[DetectionService] = None, session_factory=AsyncSessionLocal):
        self.detection_service = detection_service or DetectionService.get_instance()
        self._session_factory = session_factory

    @classmethod
    def get_instance(cls) -> "ArtifactService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_state(cls) -> None:
        """Clear state for isolated test runs."""
        cls._instance = None

    def clear(self) -> None:
        """Clear state for isolated test runs."""
        pass

    async def ingest_artifacts(
        self,
        artifacts: Union[ArtifactSubmissionRequest, ArtifactCreate, List[ArtifactCreate], Dict[str, Any], List[Dict[str, Any]]],
        job_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        plan: Optional[Dict[str, Any]] = None,
    ) -> Union[ArtifactSubmissionResponse, List[ArtifactRead]]:
        """
        Persists newly submitted forensic artifacts into PostgreSQL, then evaluates detection rules.
        Supports both ArtifactSubmissionRequest DTO and list of artifacts.
        """
        is_submission_request = isinstance(artifacts, ArtifactSubmissionRequest)
        now = datetime.now(timezone.utc)

        if is_submission_request:
            req: ArtifactSubmissionRequest = artifacts
            effective_job_id = req.job_id
            effective_agent_id = req.agent_id
            items = req.artifacts
        elif hasattr(artifacts, "artifacts"):
            # ArtifactBulkCreate or similar container
            effective_job_id = getattr(artifacts, "job_id", job_id) or "unknown-job"
            effective_agent_id = getattr(artifacts, "agent_id", agent_id) or "unknown-agent"
            items = artifacts.artifacts
        elif isinstance(artifacts, list):
            effective_job_id = job_id or "unknown-job"
            effective_agent_id = agent_id or "unknown-agent"
            items = artifacts
        else:
            effective_job_id = job_id or "unknown-job"
            effective_agent_id = agent_id or "unknown-agent"
            items = [artifacts]

        persisted: List[ArtifactRead] = []

        async with self._session_factory() as session:
            for item in items:
                if isinstance(item, dict):
                    art_id = item.get("id") or f"art-{uuid.uuid4().hex[:12]}"
                    art_job_id = item.get("job_id") or effective_job_id
                    art_agent_id = item.get("agent_id") or effective_agent_id
                    art_type = item.get("type", "unknown")
                    art_target = item.get("target")
                    art_host_id = item.get("host_id")
                    art_data = item.get("data", {})
                    art_meta = item.get("metadata", {})
                    collected_at = item.get("timestamp") or item.get("collected_at") or now
                else:
                    art_id = getattr(item, "id", None) or f"art-{uuid.uuid4().hex[:12]}"
                    art_job_id = getattr(item, "job_id", None) or effective_job_id
                    art_agent_id = getattr(item, "agent_id", None) or effective_agent_id
                    art_type = getattr(item, "type", "unknown")
                    art_target = getattr(item, "target", None)
                    art_host_id = getattr(item, "host_id", None)
                    art_data = getattr(item, "data", {})
                    art_meta = getattr(item, "metadata", {})
                    collected_at = getattr(item, "timestamp", None) or getattr(item, "collected_at", None) or now

                if isinstance(collected_at, str):
                    try:
                        collected_at = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
                    except Exception:
                        collected_at = now

                art_model = ArtifactModel(
                    id=art_id,
                    job_id=art_job_id if art_job_id != "unknown-job" else None,
                    agent_id=art_agent_id if art_agent_id != "unknown-agent" else None,
                    type=art_type,
                    target=art_target,
                    host_id=art_host_id,
                    data=art_data or {},
                    extra_metadata=art_meta or {},
                    collected_at=collected_at,
                    created_at=now,
                )
                await session.merge(art_model)

                record = ArtifactRead(
                    id=art_id,
                    job_id=art_job_id,
                    agent_id=art_agent_id,
                    type=art_type,
                    target=art_target,
                    host_id=art_host_id,
                    data=art_data or {},
                    metadata=art_meta or {},
                    collected_at=collected_at,
                    timestamp=collected_at,
                )
                persisted.append(record)

            await session.commit()

        # Trigger Detection Engine (guarded against failures)
        new_detections = []
        try:
            new_detections = await self.detection_service.process_artifacts(
                artifacts=persisted,
                job_id=effective_job_id,
                agent_id=effective_agent_id,
                plan=plan,
            )
        except Exception as e:
            logger.error(f"Detection engine error during artifact ingestion: {e}", exc_info=True)

        # Broadcast Live Events to Connected WebSocket Clients & Update Job Status
        try:
            from app.api.websocket.jobs import manager as ws_manager
            job_svc = JobService(session_factory=self._session_factory)            
            await job_svc.complete_job(effective_job_id)

            for record in persisted:
                target_job = record.job_id if record.job_id != "unknown-job" else effective_job_id
                if target_job and target_job != "unknown-job":
                    await ws_manager.broadcast_job_event(target_job, {
                        "event": "artifact_collected",
                        "job_id": target_job,
                        "agent_id": record.agent_id,
                        "timestamp": (record.collected_at or now).isoformat(),
                        "payload": {
                            "id": record.id,
                            "type": record.type,
                            "data": record.data,
                        },
                    })

            if new_detections:
                for det in new_detections:
                    target_job = det.job_id if det.job_id != "unknown-job" else effective_job_id
                    if target_job and target_job != "unknown-job":
                        await ws_manager.broadcast_job_event(target_job, {
                            "event": "threat_detected",
                            "job_id": target_job,
                            "detection": det.model_dump(mode="json"),
                        })

            if effective_job_id and effective_job_id != "unknown-job":
                await ws_manager.broadcast_job_event(effective_job_id, {
                    "event": "job_status",
                    "job_id": effective_job_id,
                    "status": "completed",
                    "timestamp": now.isoformat(),
                })
        except Exception as ws_err:
            logger.debug(f"Live job event broadcast notice: {ws_err}")

        if is_submission_request:
            return ArtifactSubmissionResponse(status="ok", ingested=len(persisted))

        return persisted

    async def list_artifacts(
        self,
        job_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        type_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ArtifactRead]:
        """Query stored forensic artifacts from database with optional filtering."""
        async with self._session_factory() as session:
            stmt = select(ArtifactModel)

            if job_id:
                stmt = stmt.where(ArtifactModel.job_id == job_id)
            if agent_id:
                stmt = stmt.where(ArtifactModel.agent_id == agent_id)
            if type_filter:
                stmt = stmt.where(func.lower(ArtifactModel.type) == type_filter.lower())

            stmt = stmt.order_by(ArtifactModel.collected_at.desc()).offset(offset).limit(limit)
            res = await session.execute(stmt)
            artifacts = res.scalars().all()

            results = []
            for a in artifacts:
                results.append(
                    ArtifactRead(
                        id=a.id,
                        job_id=a.job_id or "unknown-job",
                        agent_id=a.agent_id or "unknown-agent",
                        type=a.type,
                        target=a.target,
                        host_id=a.host_id,
                        data=a.data or {},
                        metadata=a.extra_metadata or {},
                        collected_at=a.collected_at,
                        timestamp=a.collected_at,
                    )
                )
            return results

    async def get_artifact(self, artifact_id: str) -> Optional[ArtifactRead]:
        """Retrieve a specific forensic artifact by ID from database."""
        async with self._session_factory() as session:
            a = await session.get(ArtifactModel, artifact_id)
            if a:
                return ArtifactRead(
                    id=a.id,
                    job_id=a.job_id or "unknown-job",
                    agent_id=a.agent_id or "unknown-agent",
                    type=a.type,
                    target=a.target,
                    host_id=a.host_id,
                    data=a.data or {},
                    metadata=a.extra_metadata or {},
                    collected_at=a.collected_at,
                    timestamp=a.collected_at,
                )
            return None
