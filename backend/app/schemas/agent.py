from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AgentBase(BaseModel):
    hostname: str
    os: str
    ip_address: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class AgentRegisterRequest(BaseModel):
    token: str
    hostname: str
    os: str
    arch: str
    agent_version: str


class AgentRegisterResponse(BaseModel):
    agent_id: str
    status: str
    heartbeat_interval_seconds: int = 5


class AgentRead(AgentBase):
    id: str
    status: str
    cert_fingerprint: Optional[str] = None
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    total: int
    items: List[AgentRead]
