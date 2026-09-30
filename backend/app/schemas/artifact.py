from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ArtifactItem(BaseModel):
    id: Optional[str] = None
    type: str
    target: Optional[str] = None
    timestamp: Optional[datetime] = None
    host_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactSubmissionRequest(BaseModel):
    job_id: str
    agent_id: str
    artifacts: List[ArtifactItem] = Field(default_factory=list)


class ArtifactSubmissionResponse(BaseModel):
    status: str = "ok"
    ingested: int


class ArtifactRead(BaseModel):
    id: str
    job_id: str
    agent_id: str
    type: str
    target: Optional[str] = None
    timestamp: datetime
    host_id: Optional[str] = None
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ArtifactListResponse(BaseModel):
    total: int
    items: List[ArtifactRead]
