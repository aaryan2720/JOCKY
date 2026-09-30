import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.agent import (
    AgentHeartbeatResponse,
    AgentListResponse,
    AgentRead,
    AgentRegisterRequest,
    AgentRegisterResponse,
)


class AgentService:
    """Business logic for agent fleet management, registration, and heartbeat tracking."""

    # Thread-safe in-memory store for registered agents
    _agents: Dict[str, dict] = {}

    @classmethod
    def reset_state(cls) -> None:
        """Helper for testing: reset agent state."""
        cls._agents.clear()

    async def register_agent(
        self, payload: AgentRegisterRequest, ip_address: Optional[str] = None
    ) -> AgentRegisterResponse:
        """Register or enroll a new agent."""
        hostname_clean = payload.hostname.strip().lower()
        os_clean = payload.os.strip().lower()
        agent_id = f"agent-{hostname_clean}-{os_clean}"

        now = datetime.now(timezone.utc)
        self._agents[agent_id] = {
            "id": agent_id,
            "hostname": payload.hostname,
            "os": payload.os,
            "arch": payload.arch,
            "version": payload.agent_version,
            "ip_address": ip_address or "127.0.0.1",
            "status": "online",
            "tags": ["production"],
            "cert_fingerprint": f"sha256:{uuid.uuid4().hex[:16]}",
            "last_seen": now,
        }

        return AgentRegisterResponse(
            agent_id=agent_id,
            status="enrolled",
            heartbeat_interval_seconds=5,
        )

    async def heartbeat(
        self, agent_id: str, status: Optional[str] = "online"
    ) -> AgentHeartbeatResponse:
        """Process incoming agent heartbeat and update presence status."""
        now = datetime.now(timezone.utc)
        if agent_id in self._agents:
            self._agents[agent_id]["last_seen"] = now
            self._agents[agent_id]["status"] = status or "online"
        else:
            # Auto-register agent if not present
            self._agents[agent_id] = {
                "id": agent_id,
                "hostname": agent_id,
                "os": "unknown",
                "arch": "unknown",
                "version": "0.1.0",
                "ip_address": "127.0.0.1",
                "status": status or "online",
                "tags": [],
                "cert_fingerprint": None,
                "last_seen": now,
            }

        return AgentHeartbeatResponse(status="ok", timestamp=now)

    async def list_agents(self, status: Optional[str] = None) -> List[AgentRead]:
        """List fleet agents with optional status filter."""
        agents = []
        for agent_data in self._agents.values():
            if status is None or agent_data.get("status") == status:
                agents.append(AgentRead(**agent_data))
        return agents

    async def get_agent(self, agent_id: str) -> Optional[AgentRead]:
        """Retrieve a specific agent by ID."""
        agent_data = self._agents.get(agent_id)
        if agent_data:
            return AgentRead(**agent_data)
        return None
