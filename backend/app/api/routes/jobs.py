from typing import List, Optional
from fastapi import APIRouter, Depends, status
from app.schemas.job import JobCreate, JobResponse, JobRead
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_job_service() -> JobService:
    return JobService()


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    payload: JobCreate,
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Dispatch a JOCKY execution plan to selected target agents."""
    return await service.create_and_dispatch_job(payload)


@router.get("", response_model=List[JobRead])
async def list_jobs() -> List[JobRead]:
    """List forensic jobs history."""
    return []
