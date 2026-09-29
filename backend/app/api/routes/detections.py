from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.detection import DetectionListResponse

router = APIRouter(prefix="/detections", tags=["Detections"])


@router.get("", response_model=DetectionListResponse)
async def list_detections(
    job_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
) -> DetectionListResponse:
    """Retrieve correlated threat alerts and rule matches."""
    return DetectionListResponse(total=0, items=[])
