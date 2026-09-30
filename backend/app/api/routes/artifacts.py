from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.artifact import (
    ArtifactListResponse,
    ArtifactSubmissionRequest,
    ArtifactSubmissionResponse,
)
from app.services.artifact_service import ArtifactService

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


def get_artifact_service() -> ArtifactService:
    return ArtifactService()


@router.post(
    "",
    response_model=ArtifactSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_artifacts(
    payload: ArtifactSubmissionRequest,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactSubmissionResponse:
    """Ingest forensic artifacts submitted by an agent."""
    return await service.ingest_artifacts(payload)


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    job_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    type_filter: Optional[str] = Query(None, alias="type"),
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactListResponse:
    """Retrieve collected forensic artifacts with optional filtering."""
    artifacts = await service.list_artifacts(
        job_id=job_id, agent_id=agent_id, type_filter=type_filter
    )
    return ArtifactListResponse(total=len(artifacts), items=artifacts)
