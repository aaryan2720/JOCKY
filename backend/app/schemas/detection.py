from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class DetectionBase(BaseModel):
    job_id: Optional[str] = None
    agent_id: str
    rule: str
    severity: str = "MEDIUM"
    evidence: Dict[str, Any]
    explanation: Optional[str] = None


class DetectionCreate(DetectionBase):
    pass


class DetectionRead(DetectionBase):
    id: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DetectionListResponse(BaseModel):
    total: int
    items: List[DetectionRead]
