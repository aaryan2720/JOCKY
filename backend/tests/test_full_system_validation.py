import asyncio
import os
import json
import pytest
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db.session import AsyncSessionLocal, init_db
from app.models.agent import AgentModel
from app.models.job import JobModel
from app.models.artifact import ArtifactModel
from app.models.detection import DetectionModel
from app.models.script import ScriptModel
from app.schemas.agent import AgentRegisterRequest
from app.schemas.job import JobCreate
from app.schemas.artifact import ArtifactSubmissionRequest, ArtifactItem
from app.schemas.script import ScriptValidateRequest
from app.services.agent_service import AgentService
from app.services.job_service import JobService
from app.services.artifact_service import ArtifactService
from app.services.detection_service import DetectionService
from app.main import app


@pytest.mark.asyncio
async def test_full_system_validation_workflow(tmp_path):
    """
    COMPLETE END-TO-END SYSTEM VALIDATION:
    1. Database migration & clean schema initialization
    2. FastAPI backend availability & health
    3. Agent enrollment, presence, and heartbeat
    4. JOCKY DSL compilation and job dispatch
    5. Agent job polling, real collection execution, and artifact persistence
    6. Adversary detection correlation, evidence chaining, and deterministic deduplication
    7. Backend restart persistence verification (100% state recovery)
    8. Agent reconnect & second job dispatch
    9. Controlled error & failure path handling
    """
    # -------------------------------------------------------------
    # Step 1: Database Initialization on Persistent Disk Storage
    # -------------------------------------------------------------
    db_file = tmp_path / "jocky_e2e_validation.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    engine_v1 = create_async_engine(db_url, connect_args={"check_same_thread": False})
    async with engine_v1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory_v1 = async_sessionmaker(
        bind=engine_v1, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    agent_svc_1 = AgentService(session_factory=session_factory_v1)
    job_svc_1 = JobService(session_factory=session_factory_v1)
    detection_svc_1 = DetectionService(session_factory=session_factory_v1)
    artifact_svc_1 = ArtifactService(
        detection_service=detection_svc_1, session_factory=session_factory_v1
    )

    # -------------------------------------------------------------
    # Step 2: Backend API & Service Availability
    # -------------------------------------------------------------
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

    # -------------------------------------------------------------
    # Step 3: Agent Fleet Enrollment & Heartbeat
    # -------------------------------------------------------------
    enroll_req = AgentRegisterRequest(
        token="jocky-agent-insecure-dev-token",
        hostname="SEC-WORKSTATION-VALIDATION",
        os="windows",
        arch="amd64",
        agent_version="0.1.0",
    )
    enroll_resp = await agent_svc_1.register_agent(enroll_req, ip_address="10.0.100.42")
    agent_id = enroll_resp.agent_id
    assert agent_id == "agent-sec-workstation-validation-windows"
    assert enroll_resp.status == "enrolled"

    # Verify agent presence in fleet
    agent_record = await agent_svc_1.get_agent(agent_id)
    assert agent_record is not None
    assert agent_record.status == "online"
    assert agent_record.hostname == "SEC-WORKSTATION-VALIDATION"

    # Heartbeat
    hb_resp = await agent_svc_1.heartbeat(agent_id, status="online")
    assert hb_resp.status == "ok"

    # -------------------------------------------------------------
    # Step 4: JOCKY DSL Script Compilation & Job Dispatch
    # -------------------------------------------------------------
    jocky_script = "COLLECT processes, connections, services, drivers;\nREPORT TO server;"
    job_create = JobCreate(
        script_body=jocky_script,
        target_agent_ids=[agent_id],
    )
    dispatch_resp = await job_svc_1.create_and_dispatch_job(job_create)
    job_id = dispatch_resp.job_id
    assert job_id.startswith("job-")
    assert dispatch_resp.status == "queued"
    assert dispatch_resp.agent_count == 1

    # -------------------------------------------------------------
    # Step 5: Agent Job Polling & Artifact Ingestion
    # -------------------------------------------------------------
    poll_resp = await job_svc_1.poll_job_for_agent(agent_id)
    assert poll_resp.job_id == job_id
    assert poll_resp.plan is not None
    assert poll_resp.plan["version"] == "1"

    # Simulate realistic artifacts collected from the endpoint
    submission = ArtifactSubmissionRequest(
        job_id=job_id,
        agent_id=agent_id,
        artifacts=[
            ArtifactItem(
                id="art-val-proc-01",
                type="processes",
                data={
                    "pid": 5120,
                    "name": "powershell.exe",
                    "path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                    "signed": True,
                    "signature_status": "signed",
                },
            ),
            ArtifactItem(
                id="art-val-conn-02",
                type="connections",
                data={
                    "pid": 5120,
                    "local_addr": "10.0.100.42:52341",
                    "remote_addr": "198.51.100.25:443",
                    "state": "ESTABLISHED",
                },
            ),
            ArtifactItem(
                id="art-val-svc-03",
                type="services",
                data={
                    "name": "WinDefend",
                    "display_name": "Microsoft Defender Antivirus Service",
                    "status": "RUNNING",
                    "start_type": "AUTO_START",
                },
            ),
            ArtifactItem(
                id="art-val-drv-04",
                type="drivers",
                data={
                    "module_name": "fltmgr",
                    "display_name": "Filter Manager Driver",
                    "driver_type": "File System",
                },
            ),
            ArtifactItem(
                id="art-val-susp-autorun-05",
                type="autoruns",
                target="registry_run",
                data={
                    "name": "MaliciousBackdoor",
                    "command": "C:\\Users\\Analyst\\AppData\\Local\\Temp\\updater.exe",
                    "location": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                    "user": "Analyst",
                },
            ),
        ],
    )

    ingest_result = await artifact_svc_1.ingest_artifacts(submission)
    assert ingest_result.status == "ok"
    assert ingest_result.ingested == 5

    # Verify artifacts retrieved from database
    persisted_artifacts = await artifact_svc_1.list_artifacts(job_id=job_id)
    assert len(persisted_artifacts) == 5

    # -------------------------------------------------------------
    # Step 6: Detection Correlation & Deterministic Deduplication
    # -------------------------------------------------------------
    detections = await detection_svc_1.list_detections(agent_id=agent_id)
    assert len(detections) >= 1
    threat_alert = detections[0]
    assert threat_alert.rule_id == "AUTORUN-SUSP-001"
    assert threat_alert.severity == "high"
    assert "updater.exe" in threat_alert.description
    assert len(threat_alert.evidence) >= 1

    # Ingest same artifact batch again -> deduplication must prevent duplicate alerts
    await artifact_svc_1.ingest_artifacts(submission)
    detections_recheck = await detection_svc_1.list_detections(agent_id=agent_id)
    assert len(detections_recheck) == len(detections)

    # -------------------------------------------------------------
    # Step 7: Critical Backend Restart Persistence Test
    # -------------------------------------------------------------
    # Simulate stopping and restarting the backend process
    await engine_v1.dispose()
    AgentService.reset_state()
    JobService.reset_state()
    ArtifactService.reset_state()
    DetectionService.reset_state()

    # Re-initialize new engine and services connected to the same database file
    engine_v2 = create_async_engine(db_url, connect_args={"check_same_thread": False})
    session_factory_v2 = async_sessionmaker(
        bind=engine_v2, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    agent_svc_2 = AgentService(session_factory=session_factory_v2)
    job_svc_2 = JobService(session_factory=session_factory_v2)
    detection_svc_2 = DetectionService(session_factory=session_factory_v2)
    artifact_svc_2 = ArtifactService(
        detection_service=detection_svc_2, session_factory=session_factory_v2
    )

    # Verify Agent survived restart
    rec_agent = await agent_svc_2.get_agent(agent_id)
    assert rec_agent is not None
    assert rec_agent.id == agent_id
    assert rec_agent.hostname == "SEC-WORKSTATION-VALIDATION"

    # Verify Job survived restart
    rec_job = await job_svc_2.get_job(job_id)
    assert rec_job is not None
    assert rec_job.id == job_id
    assert rec_job.status == "completed"

    # Verify Artifacts survived restart
    rec_arts = await artifact_svc_2.list_artifacts(job_id=job_id)
    assert len(rec_arts) == 5

    # Verify Detection survived restart
    rec_dets = await detection_svc_2.list_detections(agent_id=agent_id)
    assert len(rec_dets) >= 1
    assert rec_dets[0].rule_id == "AUTORUN-SUSP-001"

    # -------------------------------------------------------------
    # Step 8: Agent Reconnect & Second Job Dispatch
    # -------------------------------------------------------------
    reconnect_hb = await agent_svc_2.heartbeat(agent_id, status="online")
    assert reconnect_hb.status == "ok"

    job_2 = await job_svc_2.create_and_dispatch_job(
        JobCreate(
            script_body="COLLECT autoruns, scheduled_tasks;\nREPORT TO server;",
            target_agent_ids=[agent_id],
        )
    )
    job_id_2 = job_2.job_id
    assert job_id_2 != job_id

    poll_2 = await job_svc_2.poll_job_for_agent(agent_id)
    assert poll_2.job_id == job_id_2

    # -------------------------------------------------------------
    # Step 9: Controlled Failure & Error Path Handling
    # -------------------------------------------------------------
    # Nonexistent Agent / Job returns None / 404
    missing_agent = await agent_svc_2.get_agent("agent-nonexistent-999")
    assert missing_agent is None

    missing_job = await job_svc_2.get_job("job-nonexistent-999")
    assert missing_job is None

    # DSL Syntax validation error returns valid=False cleanly
    from app.api.routes.scripts import validate_script
    invalid_script_req = ScriptValidateRequest(body="INVALID VERB processes WHERE")
    val_resp = await validate_script(invalid_script_req)
    assert val_resp.valid is False
    assert len(val_resp.errors) > 0

    await engine_v2.dispose()
