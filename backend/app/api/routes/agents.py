from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.agent import (
    AgentListResponse,
    AgentRegisterRequest,
    AgentRegisterResponse,
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_agent_service() -> AgentService:
    return AgentService()


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    """List all registered forensic agents across the fleet."""
    agents = await service.list_agents(status=status_filter)
    return AgentListResponse(total=len(agents), items=agents)


@router.post("/register", response_model=AgentRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    payload: AgentRegisterRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentRegisterResponse:
    """Agent enrollment endpoint for bootstrapping secure communication."""
    return await service.register_agent(payload)
