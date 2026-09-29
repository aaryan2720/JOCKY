from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    script_id: Optional[str] = None
    script_body: Optional[str] = None
    target_agent_ids: List[str] = Field(default_factory=list)
    target_tags: List[str] = Field(default_factory=list)


class JobResponse(BaseModel):
    job_id: str
    status: str
    agent_count: int
    created_at: datetime


class JobRead(BaseModel):
    id: str
    script_id: Optional[str] = None
    status: str
    target_agents: List[str] = Field(default_factory=list)
    plan: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
