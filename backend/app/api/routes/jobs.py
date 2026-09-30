from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.job import JobCreate, JobResponse, JobRead
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_job_service() -> JobService:
    return JobService.get_instance()


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    payload: JobCreate,
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Dispatch a JOCKY execution plan to selected target agents."""
    return await service.create_and_dispatch_job(payload)


@router.get("", response_model=List[JobRead])
async def list_jobs(
    agent_id: Optional[str] = Query(None, description="Filter by target agent ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (queued, running, completed, failed)"),
    service: JobService = Depends(get_job_service),
) -> List[JobRead]:
    """List forensic jobs history."""
    return await service.list_jobs(agent_id=agent_id, status=status_filter)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: str,
    service: JobService = Depends(get_job_service),
) -> JobRead:
    """Retrieve details for a specific forensic execution job."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )
    return job

