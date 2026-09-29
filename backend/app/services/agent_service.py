from typing import List, Optional
from app.schemas.agent import AgentRegisterRequest, AgentRegisterResponse, AgentRead


class AgentService:
    """Business logic for agent fleet management and registration."""

    async def register_agent(self, payload: AgentRegisterRequest) -> AgentRegisterResponse:
        """Register or enroll a new agent."""
        # Future: generate mTLS certs or register in DB
        agent_id = f"agent-{payload.hostname.lower()}-{payload.os.lower()}"
        return AgentRegisterResponse(
            agent_id=agent_id,
            status="enrolled",
            heartbeat_interval_seconds=5
        )

    async def list_agents(self, status: Optional[str] = None) -> List[dict]:
        """List fleet agents with optional status filter."""
        # Stub list of mock agents for initial validation
        return []
