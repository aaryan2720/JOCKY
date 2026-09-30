from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.detection import DetectionListResponse, DetectionRead
from app.services.detection_service import DetectionService

router = APIRouter(prefix="/detections", tags=["Detections"])


def get_detection_service() -> DetectionService:
    return DetectionService.get_instance()


@router.get("", response_model=DetectionListResponse)
async def list_detections(
    agent_id: Optional[str] = Query(None, description="Filter by agent identifier"),
    job_id: Optional[str] = Query(None, description="Filter by originating job ID"),
    severity: Optional[str] = Query(None, description="Filter by detection severity (low, medium, high, critical)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by alert status (open, acknowledged, resolved)"),
    rule_id: Optional[str] = Query(None, description="Filter by detection rule ID (e.g. PROC-UNSIGNED-001)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: DetectionService = Depends(get_detection_service),
) -> DetectionListResponse:
    """Retrieve correlated threat detections and rule matches."""
    items = await service.list_detections(
        agent_id=agent_id,
        job_id=job_id,
        severity=severity,
        status=status_filter,
        rule_id=rule_id,
        limit=limit,
        offset=offset,
    )
    return DetectionListResponse(total=len(items), items=items)


@router.get("/{detection_id}", response_model=DetectionRead)
async def get_detection(
    detection_id: str,
    service: DetectionService = Depends(get_detection_service),
) -> DetectionRead:
    """Retrieve a specific threat detection and its full evidence chain."""
    det = await service.get_detection(detection_id)
    if not det:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with ID '{detection_id}' not found",
        )
    return det
