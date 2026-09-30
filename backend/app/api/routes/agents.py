from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from app.schemas.agent import (
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentListResponse,
    AgentRead,
    AgentRegisterRequest,
    AgentRegisterResponse,
)
from app.schemas.job import JobPollResponse
from app.services.agent_service import AgentService
from app.services.job_service import JobService

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_agent_service() -> AgentService:
    return AgentService.get_instance()


def get_job_service() -> JobService:
    return JobService.get_instance()


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    """List all registered forensic agents across the fleet."""
    agents = await service.list_agents(status=status_filter)
    return AgentListResponse(total=len(agents), items=agents)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    """Retrieve details for a specific registered agent."""
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID '{agent_id}' not found",
        )
    return agent


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
