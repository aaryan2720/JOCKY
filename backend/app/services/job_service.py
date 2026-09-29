from datetime import datetime
from typing import List, Optional
from app.schemas.job import JobCreate, JobResponse


class JobService:
    """Business logic for job lifecycle and dispatch coordination."""

    async def create_and_dispatch_job(self, payload: JobCreate) -> JobResponse:
        """Create a new job and orchestrate dispatch to target agents."""
        job_id = f"job-{int(datetime.utcnow().timestamp())}"
        agent_count = len(payload.target_agent_ids) or 1
        return JobResponse(
            job_id=job_id,
            status="queued",
            agent_count=agent_count,
            created_at=datetime.utcnow()
        )
