import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.jocky import compile_jocky_to_json
from app.schemas.job import JobCreate, JobPollResponse, JobRead, JobResponse
from app.services.agent_service import AgentService


class JobService:
    """Business logic for job lifecycle, JOCKY DSL compilation, and dispatch coordination."""

    _instance: Optional["JobService"] = None

    def __init__(self):
        self._jobs: Dict[str, JobRead] = {}
        self._agent_queues: Dict[str, List[str]] = defaultdict(list)
        self._init_defaults()

    @classmethod
    def get_instance(cls) -> "JobService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_state(cls) -> None:
        """Helper for testing: reset job state."""
        instance = cls.get_instance()
        instance._jobs.clear()
        instance._agent_queues.clear()

    def _init_defaults(self):
        now = datetime.now(timezone.utc)
        demo_job_1 = JobRead(
            id="job-78a9c2b0",
            script_id="script-pers-001",
            status="completed",
            target_agents=["agent-win-prod-01"],
            plan={
                "version": "1",
                "statements": [
                    {"operation": "scan", "target": "processes"},
                    {"operation": "scan", "target": "connections"},
                    {"operation": "collect", "targets": ["autoruns", "scheduled_tasks"]},
                ],
            },
            created_at=now,
            completed_at=now,
        )
        self._jobs[demo_job_1.id] = demo_job_1

    async def create_and_dispatch_job(self, payload: JobCreate) -> JobResponse:
        """Create a new job, compile JOCKY script if needed, and queue dispatch to target agents."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        # 1. Determine execution plan
        plan = payload.plan
        if not plan and payload.script_body:
            try:
                from app.jocky.parser import JockyParser
                from app.jocky.planner import JockyPlanner
                ast = JockyParser(payload.script_body).parse()
                plan = JockyPlanner(ast).build_execution_plan()
            except Exception:
                # If script compilation fails, record basic uncompiled job
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

        # 3. Store job
        job_record = JobRead(
            id=job_id,
            script_id=payload.script_id,
            status="queued",
            target_agents=target_agents,
            plan=plan,
            created_at=now,
            completed_at=None,
        )
        self._jobs[job_id] = job_record

        # 4. Enqueue for target agents
        for agent_id in target_agents:
            self._agent_queues[agent_id].append(job_id)

        return JobResponse(
            job_id=job_id,
            status="queued",
            agent_count=len(target_agents),
            created_at=now,
        )

    async def poll_job_for_agent(self, agent_id: str) -> JobPollResponse:
        """Poll next pending job for the specified agent."""
        queue = self._agent_queues[agent_id]
        while queue:
            job_id = queue.pop(0)
            job_data = self._jobs.get(job_id)
            if job_data:
                self._jobs[job_id] = job_data.model_copy(update={"status": "in_progress"})
                return JobPollResponse(
                    job_id=job_id,
                    plan=job_data.plan,
                )

        return JobPollResponse(job_id=None, plan=None)

    async def complete_job(self, job_id: str) -> None:
        """Mark job execution as completed."""
        await self.update_job_status(job_id, "completed")

    async def update_job_status(self, job_id: str, status: str) -> Optional[JobRead]:
        """Update job execution state."""
        job = self._jobs.get(job_id)
        if job:
            now = datetime.now(timezone.utc)
            completed_at = now if status in ("completed", "failed", "cancelled") else job.completed_at
            updated = job.model_copy(update={"status": status, "completed_at": completed_at})
            self._jobs[job_id] = updated
            return updated
        return None

    async def list_jobs(self, agent_id: Optional[str] = None, status: Optional[str] = None) -> List[JobRead]:
        """List forensic jobs history with optional filtering."""
        jobs = list(self._jobs.values())
        if agent_id:
            jobs = [j for j in jobs if agent_id in j.target_agents]
        if status:
            jobs = [j for j in jobs if j.status.lower() == status.lower()]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    async def get_job(self, job_id: str) -> Optional[JobRead]:
        """Retrieve a specific job by ID."""
        return self._jobs.get(job_id)
