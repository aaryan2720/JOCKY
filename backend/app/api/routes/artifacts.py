from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.artifact import ArtifactListResponse

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    job_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    type_filter: Optional[str] = Query(None, alias="type"),
) -> ArtifactListResponse:
    """Retrieve collected forensic artifacts with optional filtering."""
    return ArtifactListResponse(total=0, items=[])
