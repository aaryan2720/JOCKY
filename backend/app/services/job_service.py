import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.job import JobModel
from app.schemas.job import JobCreate, JobPollResponse, JobRead, JobResponse
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class JobService:
    """Business logic for job lifecycle, JOCKY DSL compilation, and dispatch coordination backed by PostgreSQL / SQLAlchemy."""

    _instance: Optional["JobService"] = None

    def __init__(self, session_factory=AsyncSessionLocal):
        self._session_factory = session_factory

    @classmethod
    def get_instance(cls) -> "JobService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_state(cls) -> None:
        """Helper for testing: reset singleton state."""
        cls._instance = None

    async def create_and_dispatch_job(self, payload: JobCreate) -> JobResponse:
        """Create a new job, compile JOCKY script if needed, and persist dispatch record to PostgreSQL."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        # 1. Determine execution plan
        plan = payload.plan
        if not plan and payload.script_body:
            try:
                from app.jocky.lexer import JockyLexer
                from app.jocky.parser import JockyParser
                from app.jocky.planner import JockyPlanner
                tokens = JockyLexer(payload.script_body).tokenize()
                ast = JockyParser(tokens).parse()
                plan = JockyPlanner(ast).build_execution_plan()
            except Exception as ex:
                logger.warning(f"Failed to compile script body: {ex}")
                plan = {"raw_script": payload.script_body}

        if not plan:
            # Default fallback: scan processes
            plan = {
                "version": "1",
                "statements": [
                    {
                        "operation": "scan",
                        "target": "processes",
                    }
                ],
            }

        # 2. Determine target agents
        target_agents = list(payload.target_agent_ids)
        if not target_agents:
            agent_service = AgentService.get_instance()
            all_agents = await agent_service.list_agents(status="online")
            target_agents = [a.id for a in all_agents]
            if not target_agents:
                target_agents = ["agent-win-prod-01"]

        # 3. Persist job in database
        async with self._session_factory() as session:
            job_record = JobModel(
                id=job_id,
                script_id=payload.script_id,
                status="queued",
                target_agents=target_agents,
                plan=plan,
                created_at=now,
                completed_at=None,
            )
            session.add(job_record)
            await session.commit()

        return JobResponse(
            job_id=job_id,
            status="queued",
            agent_count=len(target_agents),
            created_at=now,
        )

    async def poll_job_for_agent(self, agent_id: str) -> JobPollResponse:
        """
        Poll next pending job for the specified agent using an atomic database update
        to guarantee single assignment under concurrent agent poll requests.
        """
        from sqlalchemy import update

        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            # Query candidate queued or pending jobs
            stmt = (
                select(JobModel.id, JobModel.plan, JobModel.target_agents)
                .where(JobModel.status.in_(["queued", "pending"]))
                .order_by(JobModel.created_at.asc())
            )
            res = await session.execute(stmt)
            candidates = res.all()

            for job_id, plan, target_agents in candidates:
                targets = target_agents or []
                if not targets or agent_id in targets:
                    # Atomically claim the job using conditional row matching
                    update_stmt = (
                        update(JobModel)
                        .where(JobModel.id == job_id, JobModel.status.in_(["queued", "pending"]))
                        .values(status="in_progress", started_at=now)
                    )
                    upd_res = await session.execute(update_stmt)
                    await session.commit()
                    if upd_res.rowcount > 0:
                        return JobPollResponse(
                            job_id=job_id,
                            plan=plan,
                        )

        return JobPollResponse(job_id=None, plan=None)

    async def complete_job(self, job_id: str) -> None:
        """Mark job execution as completed in database."""
        await self.update_job_status(job_id, "completed")

    async def update_job_status(self, job_id: str, status: str) -> Optional[JobRead]:
        """Update job execution state in database."""
        async with self._session_factory() as session:
            job = await session.get(JobModel, job_id)
            if job:
                now = datetime.now(timezone.utc)
                job.status = status
                if status in ("completed", "failed", "cancelled"):
                    job.completed_at = now
                await session.commit()
                await session.refresh(job)
                return JobRead.model_validate(job)
            return None

    async def list_jobs(self, agent_id: Optional[str] = None, status: Optional[str] = None) -> List[JobRead]:
        """List forensic jobs history with optional filtering from database."""
        async with self._session_factory() as session:
            stmt = select(JobModel)
            if status:
                stmt = stmt.where(func.lower(JobModel.status) == status.lower())
            stmt = stmt.order_by(JobModel.created_at.desc())
            res = await session.execute(stmt)
            jobs = res.scalars().all()

            if agent_id:
                jobs = [j for j in jobs if j.target_agents and agent_id in j.target_agents]

            return [JobRead.model_validate(j) for j in jobs]

    async def get_job(self, job_id: str) -> Optional[JobRead]:
        """Retrieve a specific job by ID from database."""
        async with self._session_factory() as session:
            job = await session.get(JobModel, job_id)
            if job:
                return JobRead.model_validate(job)
            return None
