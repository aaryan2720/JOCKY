import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.artifact import (
    ArtifactItem,
    ArtifactListResponse,
    ArtifactRead,
    ArtifactSubmissionRequest,
    ArtifactSubmissionResponse,
)
from app.services.job_service import JobService


class ArtifactService:
    """Business logic for forensic artifact ingestion, storage, and retrieval."""

    _artifacts: List[dict] = []

    @classmethod
    def reset_state(cls) -> None:
        """Helper for testing: reset artifact state."""
        cls._artifacts.clear()

    async def ingest_artifacts(
        self, payload: ArtifactSubmissionRequest
    ) -> ArtifactSubmissionResponse:
        """Ingest forensic artifacts submitted by an agent for a job."""
        now = datetime.now(timezone.utc)
        count = 0

        for item in payload.artifacts:
            art_id = item.id or str(uuid.uuid4())
            ts = item.timestamp or now
            self._artifacts.append(
                {
                    "id": art_id,
                    "job_id": payload.job_id,
                    "agent_id": payload.agent_id,
                    "type": item.type,
                    "target": item.target,
                    "timestamp": ts,
                    "host_id": item.host_id,
                    "data": item.data,
                    "metadata": item.metadata,
                }
            )
            count += 1

        # Mark originating job as completed
        job_service = JobService()
        await job_service.complete_job(payload.job_id)

        return ArtifactSubmissionResponse(status="ok", ingested=count)

    async def list_artifacts(
        self,
        job_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> List[ArtifactRead]:
        """Retrieve collected forensic artifacts with optional filtering."""
        results = []
        for art in self._artifacts:
            if job_id and art["job_id"] != job_id:
                continue
            if agent_id and art["agent_id"] != agent_id:
                continue
            if type_filter and art["type"] != type_filter:
                continue
            results.append(ArtifactRead(**art))
        return results
