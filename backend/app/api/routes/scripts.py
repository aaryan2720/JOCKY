from typing import List
from fastapi import APIRouter, status
from app.schemas.script import (
    ScriptRead,
    ScriptCreate,
    ScriptValidateRequest,
    ScriptValidateResponse,
)

router = APIRouter(prefix="/scripts", tags=["Scripts"])


@router.get("", response_model=List[ScriptRead])
async def list_scripts() -> List[ScriptRead]:
    """List all saved JOCKY forensic scripts."""
    return []


@router.post("/validate", response_model=ScriptValidateResponse)
async def validate_script(payload: ScriptValidateRequest) -> ScriptValidateResponse:
    """Validate JOCKY DSL script syntax without executing."""
    # Stub validator response
    return ScriptValidateResponse(
        valid=True,
        ast_summary={"statements": 0},
        estimated_artifacts=[],
        errors=[]
    )
