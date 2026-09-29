from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ArtifactBase(BaseModel):
    job_id: str
    agent_id: str
    type: str
    data: Dict[str, Any]


class ArtifactCreate(ArtifactBase):
    pass


class ArtifactRead(ArtifactBase):
    id: str
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactListResponse(BaseModel):
    total: int
    items: List[ArtifactRead]
