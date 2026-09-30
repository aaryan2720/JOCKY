import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.jocky import compile_jocky_to_json
from app.schemas.job import JobCreate, JobPollResponse, JobRead, JobResponse
from app.services.agent_service import AgentService


class JobService:
    """Business logic for job lifecycle, JOCKY DSL compilation, and dispatch coordination."""

    # Thread-safe in-memory stores
    _jobs: Dict[str, dict] = {}
    _agent_queues: Dict[str, List[str]] = defaultdict(list)

    @classmethod
    def reset_state(cls) -> None:
        """Helper for testing: reset job state."""
        cls._jobs.clear()
        cls._agent_queues.clear()

    async def create_and_dispatch_job(self, payload: JobCreate) -> JobResponse:
        """Create a new job, compile JOCKY script if needed, and queue dispatch to target agents."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        # 1. Determine execution plan
        plan = payload.plan
        if not plan and payload.script_body:
            # Compile JOCKY script to structured execution plan
            plan_json_str = compile_jocky_to_json(payload.script_body)
            plan = json.loads(plan_json_str)

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
            # Target all currently registered online agents
            agent_service = AgentService()
            all_agents = await agent_service.list_agents(status="online")
            target_agents = [a.id for a in all_agents]

        # 3. Store job
        self._jobs[job_id] = {
            "id": job_id,
            "script_id": payload.script_id,
            "status": "queued",
            "target_agents": target_agents,
            "plan": plan,
            "created_at": now,
            "completed_at": None,
        }

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
                job_data["status"] = "in_progress"
                return JobPollResponse(
                    job_id=job_id,
                    plan=job_data.get("plan"),
                )

        return JobPollResponse(job_id=None, plan=None)

    async def complete_job(self, job_id: str) -> None:
        """Mark job execution as completed."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "completed"
            self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc)

    async def list_jobs(self) -> List[JobRead]:
        """List forensic jobs history."""
        return [JobRead(**job_data) for job_data in self._jobs.values()]

    async def get_job(self, job_id: str) -> Optional[JobRead]:
        """Retrieve a job by ID."""
        job_data = self._jobs.get(job_id)
        if job_data:
            return JobRead(**job_data)
        return None
