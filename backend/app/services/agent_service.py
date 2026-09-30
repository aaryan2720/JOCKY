import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.agent import AgentModel
from app.schemas.agent import (
    AgentHeartbeatResponse,
    AgentListResponse,
    AgentRead,
    AgentRegisterRequest,
    AgentRegisterResponse,
)

logger = logging.getLogger(__name__)


class AgentService:
    """Business logic for agent fleet management, registration, and heartbeat tracking backed by PostgreSQL / SQLAlchemy."""

    _instance: Optional["AgentService"] = None

    def __init__(self, session_factory=AsyncSessionLocal):
        self._session_factory = session_factory

    @classmethod
    def get_instance(cls) -> "AgentService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_state(cls) -> None:
        """Helper for testing: reset agent state in singleton."""
        cls._instance = None

    async def seed_defaults_if_empty(self) -> None:
        """Seed default demo agents if database is empty."""
        async with self._session_factory() as session:
            res = await session.execute(select(func.count(AgentModel.id)))
            count = res.scalar() or 0
            if count == 0:
                now = datetime.now(timezone.utc)
                defaults = [
                    AgentModel(
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
                        created_at=now,
                    ),
                    AgentModel(
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
                        created_at=now,
                    ),
                ]
                session.add_all(defaults)
                await session.commit()

    async def register_agent(
        self, payload: AgentRegisterRequest, ip_address: Optional[str] = None
    ) -> AgentRegisterResponse:
        """Register or enroll a new agent into PostgreSQL persistence."""
        hostname_clean = payload.hostname.strip().lower()
        os_clean = payload.os.strip().lower()
        agent_id = f"agent-{hostname_clean}-{os_clean}"

        now = datetime.now(timezone.utc)
        fingerprint = "sha256:" + hashlib.sha256(f"{agent_id}:{payload.token}".encode()).hexdigest()[:16]

        async with self._session_factory() as session:
            existing = await session.get(AgentModel, agent_id)
            if existing:
                existing.hostname = payload.hostname
                existing.os = payload.os
                existing.arch = payload.arch
                existing.ip_address = ip_address or "127.0.0.1"
                existing.version = payload.agent_version
                existing.tags = ["enrolled", payload.os.lower()]
                existing.status = "online"
                existing.last_seen = now
                existing.cert_fingerprint = fingerprint
            else:
                new_agent = AgentModel(
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
                    created_at=now,
                )
                session.add(new_agent)
            await session.commit()

        return AgentRegisterResponse(
            agent_id=agent_id,
            status="enrolled",
            heartbeat_interval_seconds=5,
        )

    async def heartbeat(
        self, agent_id: str, status: Optional[str] = "online"
    ) -> AgentHeartbeatResponse:
        """Process incoming agent heartbeat and update presence status in database."""
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            agent = await session.get(AgentModel, agent_id)
            if agent:
                agent.last_seen = now
                agent.status = status or "online"
            else:
                # Auto-register agent if not yet present
                agent = AgentModel(
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
                    created_at=now,
                )
                session.add(agent)
            await session.commit()

        return AgentHeartbeatResponse(status="ok", timestamp=now)

    async def list_agents(self, status: Optional[str] = None) -> List[AgentRead]:
        """List fleet agents with optional status filter from persistent database."""
        await self.seed_defaults_if_empty()
        async with self._session_factory() as session:
            stmt = select(AgentModel)
            if status:
                stmt = stmt.where(func.lower(AgentModel.status) == status.lower())
            stmt = stmt.order_by(AgentModel.last_seen.desc())
            res = await session.execute(stmt)
            agents = res.scalars().all()
            return [AgentRead.model_validate(a) for a in agents]

    async def get_agent(self, agent_id: str) -> Optional[AgentRead]:
        """Retrieve a specific agent by ID from database."""
        async with self._session_factory() as session:
            agent = await session.get(AgentModel, agent_id)
            if agent:
                return AgentRead.model_validate(agent)
            return None
