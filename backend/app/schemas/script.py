from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ScriptBase(BaseModel):
    name: str
    description: Optional[str] = None
    body: str


class ScriptCreate(ScriptBase):
    pass


class ScriptValidateRequest(BaseModel):
    body: str


class ScriptValidateResponse(BaseModel):
    valid: bool
    ast_summary: Optional[Dict[str, Any]] = None
    estimated_artifacts: List[str] = []
    errors: List[str] = []


class ScriptRead(ScriptBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
