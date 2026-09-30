import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, status
from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models.script import ScriptModel
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


async def _init_default_scripts_db():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(func.count(ScriptModel.id)))
        count = res.scalar() or 0
        if count == 0:
            now = datetime.now(timezone.utc)
            defaults = [
                ScriptModel(
                    id="script-pers-001",
                    name="Endpoint Persistence Triage",
                    description="Collects autostart entries, Run keys, startup files, and scheduled tasks / cron jobs.",
                    body="COLLECT autoruns;\nCOLLECT scheduled_tasks;",
                    created_by="Analyst",
                    created_at=now,
                    updated_at=now,
                ),
                ScriptModel(
                    id="script-proc-net-002",
                    name="Unsigned Process & Network Hunt",
                    description="Scans for unsigned executables and collects active socket connections across the fleet.",
                    body="SCAN processes WHERE signed == false;\nCOLLECT connections;",
                    created_by="Analyst",
                    created_at=now,
                    updated_at=now,
                ),
                ScriptModel(
                    id="script-identity-003",
                    name="Identity & Active Session Audit",
                    description="Enumerates local user accounts and actively logged-in terminal/remote sessions.",
                    body="COLLECT users;\nCOLLECT sessions;",
                    created_by="Analyst",
                    created_at=now,
                    updated_at=now,
                ),
                ScriptModel(
                    id="script-full-004",
                    name="Comprehensive Forensic Sweep",
                    description="Collects all active collectors: processes, connections, autoruns, scheduled tasks, users, and sessions.",
                    body="COLLECT processes;\nCOLLECT connections;\nCOLLECT autoruns;\nCOLLECT scheduled_tasks;\nCOLLECT users;\nCOLLECT sessions;",
                    created_by="Analyst",
                    created_at=now,
                    updated_at=now,
                ),
            ]
            session.add_all(defaults)
            await session.commit()


@router.get("", response_model=List[ScriptRead])
async def list_scripts() -> List[ScriptRead]:
    """List all saved JOCKY forensic scripts from database."""
    await _init_default_scripts_db()
    async with AsyncSessionLocal() as session:
        stmt = select(ScriptModel).order_by(ScriptModel.created_at.asc())
        res = await session.execute(stmt)
        scripts = res.scalars().all()
        return [
            ScriptRead(
                id=s.id,
                name=s.name,
                description=s.description,
                body=s.body,
                created_by=s.created_by,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in scripts
        ]


@router.post("", response_model=ScriptRead, status_code=status.HTTP_201_CREATED)
async def create_script(payload: ScriptCreate) -> ScriptRead:
    """Save a new JOCKY forensic investigation script in database."""
    await _init_default_scripts_db()
    now = datetime.now(timezone.utc)
    script_id = f"script-{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as session:
        script = ScriptModel(
            id=script_id,
            name=payload.name,
            description=payload.description,
            body=payload.body,
            created_by="Analyst",
            created_at=now,
            updated_at=now,
        )
        session.add(script)
        await session.commit()

    return ScriptRead(
        id=script_id,
        name=payload.name,
        description=payload.description,
        body=payload.body,
        created_by="Analyst",
        created_at=now,
        updated_at=now,
    )


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
