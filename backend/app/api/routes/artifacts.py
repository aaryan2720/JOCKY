from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from app.schemas.artifact import (
    ArtifactBulkCreate,
    ArtifactCreate,
    ArtifactListResponse,
    ArtifactRead,
    ArtifactSubmissionRequest,
    ArtifactSubmissionResponse,
)
from app.services.artifact_service import ArtifactService

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


def get_artifact_service() -> ArtifactService:
    return ArtifactService.get_instance()


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    job_id: Optional[str] = Query(None, description="Filter by originating job ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent identifier"),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by artifact type (process, network, etc.)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactListResponse:
    """Retrieve collected forensic artifacts with optional filtering."""
    items = await service.list_artifacts(
        job_id=job_id,
        agent_id=agent_id,
        type_filter=type_filter,
        limit=limit,
        offset=offset,
    )
    return ArtifactListResponse(total=len(items), items=items)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def submit_artifacts(
    payload: Union[ArtifactSubmissionRequest, ArtifactBulkCreate, List[ArtifactCreate], ArtifactCreate, Dict[str, Any]] = Body(...),
    service: ArtifactService = Depends(get_artifact_service),
) -> Any:
    """Ingest forensic artifacts submitted by an agent."""
    res = await service.ingest_artifacts(payload)
    return res


@router.get("/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(
    artifact_id: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactRead:
    """Retrieve a single forensic artifact by ID."""
    art = await service.get_artifact(artifact_id)
    if not art:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID '{artifact_id}' not found",
        )
    return art
