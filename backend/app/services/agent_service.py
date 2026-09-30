import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict
from app.schemas.agent import AgentRegisterRequest, AgentRegisterResponse, AgentRead


class AgentService:
    """Business logic for agent fleet management and registration."""

    _instance: Optional["AgentService"] = None

    def __init__(self):
        self._agents: Dict[str, AgentRead] = {}
        self._init_defaults()

    @classmethod
    def get_instance(cls) -> "AgentService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_defaults(self):
        now = datetime.now(timezone.utc)
        defaults = [
            AgentRead(
                id="agent-win-prod-01",
                hostname="SEC-FIN-WIN11",
                os="windows",
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

    async def register_agent(self, payload: AgentRegisterRequest) -> AgentRegisterResponse:
        """Register or enroll a new agent."""
        agent_id = f"agent-{payload.hostname.lower()}-{payload.os.lower()}"
        now = datetime.now(timezone.utc)
        fingerprint = "sha256:" + hashlib.sha256(f"{agent_id}:{payload.token}".encode()).hexdigest()[:16]
        agent_record = AgentRead(
            id=agent_id,
            hostname=payload.hostname,
            os=payload.os,
            ip_address="127.0.0.1",
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
            heartbeat_interval_seconds=5
        )

    async def list_agents(self, status: Optional[str] = None) -> List[AgentRead]:
        """List fleet agents with optional status filter."""
        agents = list(self._agents.values())
        if status:
            agents = [a for a in agents if a.status.lower() == status.lower()]
        return agents

    async def get_agent(self, agent_id: str) -> Optional[AgentRead]:
        """Get an agent by its ID."""
        return self._agents.get(agent_id)

