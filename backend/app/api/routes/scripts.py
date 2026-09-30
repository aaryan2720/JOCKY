import uuid
from datetime import datetime, timezone
from typing import List, Dict
from fastapi import APIRouter, status
from app.schemas.script import (
    ScriptRead,
    ScriptCreate,
    ScriptValidateRequest,
    ScriptValidateResponse,
)
from app.jocky.lexer import JockyLexer
from app.jocky.parser import JockyParser
from app.jocky.planner import JockyPlanner

router = APIRouter(prefix="/scripts", tags=["Scripts"])

_SAVED_SCRIPTS: Dict[str, ScriptRead] = {}


def _init_default_scripts():
    if _SAVED_SCRIPTS:
        return
    now = datetime.now(timezone.utc)
    defaults = [
        ScriptRead(
            id="script-pers-001",
            name="Endpoint Persistence Triage",
            description="Collects autostart entries, Run keys, startup files, and scheduled tasks / cron jobs.",
            body="COLLECT autoruns;\nCOLLECT scheduled_tasks;",
            created_by="Analyst",
            created_at=now,
            updated_at=now,
        ),
        ScriptRead(
            id="script-proc-net-002",
            name="Unsigned Process & Network Hunt",
            description="Scans for unsigned executables and collects active socket connections across the fleet.",
            body="SCAN processes WHERE signed == false;\nCOLLECT connections;",
            created_by="Analyst",
            created_at=now,
            updated_at=now,
        ),
        ScriptRead(
            id="script-identity-003",
            name="Identity & Active Session Audit",
            description="Enumerates local user accounts and actively logged-in terminal/remote sessions.",
            body="COLLECT users;\nCOLLECT sessions;",
            created_by="Analyst",
            created_at=now,
            updated_at=now,
        ),
        ScriptRead(
            id="script-full-004",
            name="Comprehensive Forensic Sweep",
            description="Collects all active collectors: processes, connections, autoruns, scheduled tasks, users, and sessions.",
            body="COLLECT processes;\nCOLLECT connections;\nCOLLECT autoruns;\nCOLLECT scheduled_tasks;\nCOLLECT users;\nCOLLECT sessions;",
            created_by="Analyst",
            created_at=now,
            updated_at=now,
        ),
    ]
    for s in defaults:
        _SAVED_SCRIPTS[s.id] = s


@router.get("", response_model=List[ScriptRead])
async def list_scripts() -> List[ScriptRead]:
    """List all saved JOCKY forensic scripts."""
    _init_default_scripts()
    return list(_SAVED_SCRIPTS.values())


@router.post("", response_model=ScriptRead, status_code=status.HTTP_201_CREATED)
async def create_script(payload: ScriptCreate) -> ScriptRead:
    """Save a new JOCKY forensic investigation script."""
    _init_default_scripts()
    now = datetime.now(timezone.utc)
    script_id = f"script-{uuid.uuid4().hex[:8]}"
    script = ScriptRead(
        id=script_id,
        name=payload.name,
        description=payload.description,
        body=payload.body,
        created_by="Analyst",
        created_at=now,
        updated_at=now,
    )
    _SAVED_SCRIPTS[script_id] = script
    return script


@router.post("/validate", response_model=ScriptValidateResponse)
async def validate_script(payload: ScriptValidateRequest) -> ScriptValidateResponse:
    """Validate JOCKY DSL script syntax without executing."""
    try:
        lexer = JockyLexer(payload.body)
        tokens = lexer.tokenize()
        parser = JockyParser(tokens)
        ast = parser.parse()
        planner = JockyPlanner(ast)
        plan = planner.build_execution_plan()
        collectors = [c.get("target") or c.get("name") if isinstance(c, dict) else str(c) for c in plan.get("collectors", [])]
        return ScriptValidateResponse(
            valid=True,
            ast_summary={
                "statements": len(ast.statements),
                "plan_version": plan.get("plan_version", "1.0"),
            },
            estimated_artifacts=collectors,
            errors=[],
        )
    except Exception as e:
        return ScriptValidateResponse(
            valid=False,
            ast_summary=None,
            estimated_artifacts=[],
            errors=[str(e)],
        )

