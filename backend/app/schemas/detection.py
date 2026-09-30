from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class EvidenceReference(BaseModel):
    artifact_id: str
    type: str
    details: Optional[Dict[str, Any]] = None


class DetectionBase(BaseModel):
    agent_id: str
    job_id: Optional[str] = None
    severity: str = "high"  # low, medium, high, critical
    title: str
    description: Optional[str] = None
    rule_id: str
    status: str = "open"  # open, acknowledged, resolved, false_positive
    evidence: List[EvidenceReference] = Field(default_factory=list)


class DetectionCreate(DetectionBase):
    pass


class DetectionRead(DetectionBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DetectionListResponse(BaseModel):
    total: int
    items: List[DetectionRead]
