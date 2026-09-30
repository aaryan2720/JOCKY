from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ArtifactBase(BaseModel):
    job_id: str
    agent_id: str
    type: str
    target: Optional[str] = None
    host_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactCreate(ArtifactBase):
    id: Optional[str] = None
    collected_at: Optional[datetime] = None
    timestamp: Optional[datetime] = None


class ArtifactItem(BaseModel):
    id: Optional[str] = None
    type: str
    target: Optional[str] = None
    timestamp: Optional[datetime] = None
    collected_at: Optional[datetime] = None
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
    timestamp: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    host_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ArtifactBulkCreate(BaseModel):
    artifacts: List[ArtifactCreate]


class ArtifactListResponse(BaseModel):
    total: int
    items: List[ArtifactRead]
