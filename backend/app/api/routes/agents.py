from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from app.schemas.agent import (
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentListResponse,
    AgentRegisterRequest,
    AgentRegisterResponse,
)
from app.schemas.job import JobPollResponse
from app.services.agent_service import AgentService
from app.services.job_service import JobService

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_agent_service() -> AgentService:
    return AgentService()


def get_job_service() -> JobService:
    return JobService()


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    """List all registered forensic agents across the fleet."""
    agents = await service.list_agents(status=status_filter)
    return AgentListResponse(total=len(agents), items=agents)


@router.post(
    "/register",
    response_model=AgentRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_agent(
    payload: AgentRegisterRequest,
    request: Request,
    service: AgentService = Depends(get_agent_service),
) -> AgentRegisterResponse:
    """Agent enrollment endpoint for bootstrapping secure communication."""
    client_host = request.client.host if request.client else "127.0.0.1"
    return await service.register_agent(payload, ip_address=client_host)


@router.post("/{agent_id}/heartbeat", response_model=AgentHeartbeatResponse)
async def send_heartbeat(
    agent_id: str,
    payload: Optional[AgentHeartbeatRequest] = None,
    service: AgentService = Depends(get_agent_service),
) -> AgentHeartbeatResponse:
    """Process heartbeat from a registered agent to maintain online presence."""
    agent_status = payload.status if payload else "online"
    return await service.heartbeat(agent_id, status=agent_status)


@router.get("/{agent_id}/jobs/poll", response_model=JobPollResponse)
async def poll_agent_job(
    agent_id: str,
    job_service: JobService = Depends(get_job_service),
) -> JobPollResponse:
    """Agent long-poll endpoint to retrieve queued forensic execution plans."""
    return await job_service.poll_job_for_agent(agent_id)
