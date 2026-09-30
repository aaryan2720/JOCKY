from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ArtifactBase(BaseModel):
    job_id: str
    agent_id: str
    type: str
    data: Dict[str, Any]


class ArtifactCreate(ArtifactBase):
    id: Optional[str] = None
    collected_at: Optional[datetime] = None


class ArtifactRead(ArtifactBase):
    id: str
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactBulkCreate(BaseModel):
    artifacts: List[ArtifactCreate]


class ArtifactListResponse(BaseModel):
    total: int
    items: List[ArtifactRead]
