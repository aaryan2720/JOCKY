from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.agent import (
    AgentListResponse,
    AgentRegisterRequest,
    AgentRegisterResponse,
    AgentRead,
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_agent_service() -> AgentService:
    return AgentService.get_instance()


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


@router.post("/register", response_model=AgentRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    payload: AgentRegisterRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentRegisterResponse:
    """Agent enrollment endpoint for bootstrapping secure communication."""
    return await service.register_agent(payload)

