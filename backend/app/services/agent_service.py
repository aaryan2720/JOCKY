import hashlib
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

    _instance: Optional["AgentService"] = None

    def __init__(self):
        self._agents: Dict[str, AgentRead] = {}
        self._init_defaults()

    @classmethod
    def get_instance(cls) -> "AgentService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_state(cls) -> None:
        """Helper for testing: reset agent state."""
        instance = cls.get_instance()
        instance._agents.clear()

    def _init_defaults(self):
        now = datetime.now(timezone.utc)
        defaults = [
            AgentRead(
                id="agent-win-prod-01",
                hostname="SEC-FIN-WIN11",
                os="windows",
                arch="amd64",
                ip_address="10.0.12.44",
                version="0.1.0",
                tags=["workstation", "finance", "prod"],
                status="online",
                last_seen=now,
                cert_fingerprint="sha256:7b91d2e84a210f9a",
            ),
            AgentRead(
                id="agent-lin-srv-02",
                hostname="PROD-KUBE-NODE-01",
                os="linux",
                arch="amd64",
                ip_address="10.0.24.102",
                version="0.1.0",
                tags=["server", "kubernetes", "infrastructure"],
                status="online",
                last_seen=now,
                cert_fingerprint="sha256:4c129e013f9988e1",
            ),
        ]
        for a in defaults:
            self._agents[a.id] = a

    async def register_agent(
        self, payload: AgentRegisterRequest, ip_address: Optional[str] = None
    ) -> AgentRegisterResponse:
        """Register or enroll a new agent."""
        hostname_clean = payload.hostname.strip().lower()
        os_clean = payload.os.strip().lower()
        agent_id = f"agent-{hostname_clean}-{os_clean}"

        now = datetime.now(timezone.utc)
        fingerprint = "sha256:" + hashlib.sha256(f"{agent_id}:{payload.token}".encode()).hexdigest()[:16]
        agent_record = AgentRead(
            id=agent_id,
            hostname=payload.hostname,
            os=payload.os,
            arch=payload.arch,
            ip_address=ip_address or "127.0.0.1",
            version=payload.agent_version,
            tags=["enrolled", payload.os.lower()],
            status="online",
            last_seen=now,
            cert_fingerprint=fingerprint,
        )
        self._agents[agent_id] = agent_record

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
            agent = self._agents[agent_id]
            self._agents[agent_id] = agent.model_copy(update={"last_seen": now, "status": status or "online"})
        else:
            # Auto-register agent if not present
            self._agents[agent_id] = AgentRead(
                id=agent_id,
                hostname=agent_id,
                os="unknown",
                arch="unknown",
                version="0.1.0",
                ip_address="127.0.0.1",
                status=status or "online",
                tags=[],
                cert_fingerprint=None,
                last_seen=now,
            )

        return AgentHeartbeatResponse(status="ok", timestamp=now)

    async def list_agents(self, status: Optional[str] = None) -> List[AgentRead]:
        """List fleet agents with optional status filter."""
        agents = list(self._agents.values())
        if status:
            agents = [a for a in agents if a.status.lower() == status.lower()]
        return agents

    async def get_agent(self, agent_id: str) -> Optional[AgentRead]:
        """Retrieve a specific agent by ID."""
        return self._agents.get(agent_id)
