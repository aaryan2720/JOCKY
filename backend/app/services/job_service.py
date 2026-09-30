import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.schemas.job import JobCreate, JobResponse, JobRead
from app.jocky.lexer import JockyLexer
from app.jocky.parser import JockyParser
from app.jocky.planner import JockyPlanner


class JobService:
    """Business logic for job lifecycle and dispatch coordination."""

    _instance: Optional["JobService"] = None

    def __init__(self):
        self._jobs: Dict[str, JobRead] = {}
        self._init_defaults()

    @classmethod
    def get_instance(cls) -> "JobService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_defaults(self):
        now = datetime.now(timezone.utc)
        demo_job_1 = JobRead(
            id="job-78a9c2b0",
            script_id="script-pers-001",
            status="completed",
            target_agents=["agent-win-prod-01"],
            plan={
                "plan_version": "1.0",
                "collectors": [
                    {"target": "processes"},
                    {"target": "connections"},
                    {"target": "autoruns"},
                    {"target": "scheduled_tasks"},
                ],
            },
            created_at=now,
            completed_at=now,
        )
        self._jobs[demo_job_1.id] = demo_job_1

    async def create_and_dispatch_job(self, payload: JobCreate) -> JobResponse:
        """Create a new job and orchestrate dispatch to target agents."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        agent_count = len(payload.target_agent_ids) or 1

        plan = None
        if payload.script_body:
            try:
                tokens = JockyLexer(payload.script_body).tokenize()
                ast = JockyParser(tokens).parse()
                plan = JockyPlanner(ast).build_execution_plan()
            except Exception:
                # If script compilation fails, record basic uncompiled job
                plan = {"raw_script": payload.script_body}

        job_record = JobRead(
            id=job_id,
            script_id=payload.script_id,
            status="queued",
            target_agents=payload.target_agent_ids or ["agent-win-prod-01"],
            plan=plan,
            created_at=now,
            completed_at=None,
        )
        self._jobs[job_id] = job_record

        return JobResponse(
            job_id=job_id,
            status="queued",
            agent_count=agent_count,
            created_at=now,
        )

    async def list_jobs(self, agent_id: Optional[str] = None, status: Optional[str] = None) -> List[JobRead]:
        """List jobs history with optional filtering."""
        jobs = list(self._jobs.values())
        if agent_id:
            jobs = [j for j in jobs if agent_id in j.target_agents]
        if status:
            jobs = [j for j in jobs if j.status.lower() == status.lower()]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    async def get_job(self, job_id: str) -> Optional[JobRead]:
        """Retrieve a single job by ID."""
        return self._jobs.get(job_id)

    async def update_job_status(self, job_id: str, status: str) -> Optional[JobRead]:
        """Update job execution state."""
        job = self._jobs.get(job_id)
        if job:
            now = datetime.now(timezone.utc)
            completed_at = now if status in ("completed", "failed", "cancelled") else job.completed_at
            updated = JobRead(
                id=job.id,
                script_id=job.script_id,
                status=status,
                target_agents=job.target_agents,
                plan=job.plan,
                created_at=job.created_at,
                completed_at=completed_at,
            )
            self._jobs[job_id] = updated
            return updated
        return None

