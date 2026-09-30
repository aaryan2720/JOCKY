import asyncio
import os
import pytest
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine, init_db
from app.models.agent import AgentModel
from app.models.job import JobModel
from app.models.artifact import ArtifactModel
from app.models.detection import DetectionModel
from app.models.script import ScriptModel
from app.schemas.agent import AgentRegisterRequest
from app.schemas.job import JobCreate
from app.schemas.artifact import ArtifactSubmissionRequest, ArtifactItem
from app.services.agent_service import AgentService
from app.services.job_service import JobService
from app.services.artifact_service import ArtifactService
from app.services.detection_service import DetectionService
from app.main import app


@pytest.mark.asyncio
async def test_agent_registration_and_heartbeat_persistence():
    """Verify agent enrollment and presence heartbeat persist in database."""
    agent_svc = AgentService()
    reg_req = AgentRegisterRequest(
        token="jocky-agent-insecure-dev-token",
        hostname="SEC-AGENT-PERSIST-01",
        os="windows",
        arch="amd64",
        agent_version="0.1.0",
    )
    reg_resp = await agent_svc.register_agent(reg_req, ip_address="192.168.1.50")
    agent_id = reg_resp.agent_id
    assert agent_id == "agent-sec-agent-persist-01-windows"

    # Query directly from DB session
    async with AsyncSessionLocal() as session:
        db_agent = await session.get(AgentModel, agent_id)
        assert db_agent is not None
        assert db_agent.hostname == "SEC-AGENT-PERSIST-01"
        assert db_agent.os == "windows"
        assert db_agent.arch == "amd64"
        assert db_agent.ip_address == "192.168.1.50"
        assert db_agent.status == "online"

    # Send heartbeat
    await agent_svc.heartbeat(agent_id, status="busy")
    async with AsyncSessionLocal() as session:
        db_agent = await session.get(AgentModel, agent_id)
        assert db_agent.status == "busy"


@pytest.mark.asyncio
async def test_job_lifecycle_and_polling_persistence():
    """Verify job creation, persistent queueing, polling, and status transitions."""
    agent_svc = AgentService()
    job_svc = JobService()

    reg_req = AgentRegisterRequest(
        token="jocky-agent-insecure-dev-token",
        hostname="JOB-TEST-NODE",
        os="linux",
        arch="amd64",
        agent_version="0.1.0",
    )
    reg_resp = await agent_svc.register_agent(reg_req)
    agent_id = reg_resp.agent_id

    # Create and dispatch job
    job_create = JobCreate(
        script_body="SCAN processes WHERE signed == false; COLLECT connections;",
        target_agent_ids=[agent_id],
    )
    job_resp = await job_svc.create_and_dispatch_job(job_create)
    job_id = job_resp.job_id

    # Verify persisted in database
    async with AsyncSessionLocal() as session:
        db_job = await session.get(JobModel, job_id)
        assert db_job is not None
        assert db_job.status == "queued"
        assert agent_id in db_job.target_agents

    # Poll job for target agent
    poll_resp = await job_svc.poll_job_for_agent(agent_id)
    assert poll_resp.job_id == job_id
    assert poll_resp.plan is not None

    # Status should transition to in_progress in DB
    async with AsyncSessionLocal() as session:
        db_job = await session.get(JobModel, job_id)
        assert db_job.status == "in_progress"
        assert db_job.started_at is not None

    # Complete job
    await job_svc.complete_job(job_id)
    async with AsyncSessionLocal() as session:
        db_job = await session.get(JobModel, job_id)
        assert db_job.status == "completed"
        assert db_job.completed_at is not None


@pytest.mark.asyncio
async def test_artifact_ingestion_and_detection_correlation_persistence():
    """Verify artifact persistence and deterministic threat detection correlation."""
    agent_svc = AgentService()
    job_svc = JobService()
    artifact_svc = ArtifactService()
    detection_svc = DetectionService()

    agent_id = "agent-hunt-persist-01"
    await agent_svc.heartbeat(agent_id)

    job_create = JobCreate(
        script_body="COLLECT autoruns;",
        target_agent_ids=[agent_id],
    )
    job_resp = await job_svc.create_and_dispatch_job(job_create)
    job_id = job_resp.job_id

    # Submit artifact with suspicious autorun executing from temp directory
    submission = ArtifactSubmissionRequest(
        job_id=job_id,
        agent_id=agent_id,
        artifacts=[
            ArtifactItem(
                id="art-persist-test-01",
                type="autoruns",
                target="registry_run",
                data={
                    "name": "PersistenceKey",
                    "command": "C:\\Users\\Victim\\AppData\\Local\\Temp\\mimikatz.exe",
                    "location": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                },
            )
        ],
    )

    ingest_resp = await artifact_svc.ingest_artifacts(submission)
    assert ingest_resp.status == "ok"
    assert ingest_resp.ingested == 1

    # Verify artifact in database
    async with AsyncSessionLocal() as session:
        db_art = await session.get(ArtifactModel, "art-persist-test-01")
        assert db_art is not None
        assert db_art.type == "autoruns"
        assert db_art.target == "registry_run"
        assert "mimikatz.exe" in db_art.data["command"]

    # Verify detection generated and persisted in database
    detections = await detection_svc.list_detections(agent_id=agent_id)
    assert len(detections) >= 1
    det = detections[0]
    assert det.agent_id == agent_id
    assert det.severity == "high"

    async with AsyncSessionLocal() as session:
        db_det = await session.get(DetectionModel, det.id)
        assert db_det is not None
        assert db_det.rule_id == det.rule_id
        assert db_det.dedup_key is not None


@pytest.mark.asyncio
async def test_detection_deduplication_deterministic_persistence():
    """Verify deduplication avoids inserting duplicate detections for the same event."""
    detection_svc = DetectionService()
    artifact_svc = ArtifactService()

    agent_id = "agent-dedup-01"
    job_id = "job-dedup-01"

    submission1 = ArtifactSubmissionRequest(
        job_id=job_id,
        agent_id=agent_id,
        artifacts=[
            ArtifactItem(
                id="art-dedup-01",
                type="processes",
                data={
                    "pid": 4040,
                    "name": "beacon.exe",
                    "path": "C:\\Windows\\Temp\\beacon.exe",
                    "signature_status": "unsigned",
                },
            )
        ],
    )
    await artifact_svc.ingest_artifacts(submission1)

    dets_after_first = await detection_svc.list_detections(agent_id=agent_id)
    count_first = len(dets_after_first)
    assert count_first >= 1

    # Ingest same artifact again (re-submission or replay)
    await artifact_svc.ingest_artifacts(submission1)

    dets_after_second = await detection_svc.list_detections(agent_id=agent_id)
    assert len(dets_after_second) == count_first


@pytest.mark.asyncio
async def test_foreign_key_and_filters():
    """Verify database foreign-key relationships and multi-criteria filters."""
    agent_svc = AgentService()
    job_svc = JobService()
    artifact_svc = ArtifactService()

    agent_id = "agent-fk-test-01"
    await agent_svc.heartbeat(agent_id)

    job_resp = await job_svc.create_and_dispatch_job(
        JobCreate(plan={"version": "1", "statements": []}, target_agent_ids=[agent_id])
    )
    job_id = job_resp.job_id

    await artifact_svc.ingest_artifacts(
        ArtifactSubmissionRequest(
            job_id=job_id,
            agent_id=agent_id,
            artifacts=[
                ArtifactItem(id="art-fk-01", type="services", data={"name": "SuspSvc"}),
                ArtifactItem(id="art-fk-02", type="drivers", data={"name": "SuspDrv"}),
            ],
        )
    )

    # Filter by type
    svc_arts = await artifact_svc.list_artifacts(agent_id=agent_id, type_filter="services")
    assert len(svc_arts) == 1
    assert svc_arts[0].type == "services"

    drv_arts = await artifact_svc.list_artifacts(agent_id=agent_id, type_filter="drivers")
    assert len(drv_arts) == 1
    assert drv_arts[0].type == "drivers"


@pytest.mark.asyncio
async def test_concurrent_job_polling_single_assignment():
    """Ensure concurrent agent polling cannot assign the same job to multiple workers."""
    agent_svc = AgentService()
    job_svc = JobService()

    agent_id = "agent-concurrent-01"
    await agent_svc.heartbeat(agent_id)

    # Create a single job
    job_resp = await job_svc.create_and_dispatch_job(
        JobCreate(plan={"version": "1", "statements": []}, target_agent_ids=[agent_id])
    )
    job_id = job_resp.job_id

    # Spawn 5 concurrent polling workers simultaneously for the same agent
    poll_results = await asyncio.gather(
        job_svc.poll_job_for_agent(agent_id),
        job_svc.poll_job_for_agent(agent_id),
        job_svc.poll_job_for_agent(agent_id),
        job_svc.poll_job_for_agent(agent_id),
        job_svc.poll_job_for_agent(agent_id),
    )

    # Exactly ONE worker should receive the job, the others must receive None
    assigned = [r for r in poll_results if r.job_id == job_id]
    unassigned = [r for r in poll_results if r.job_id is None]

    assert len(assigned) == 1
    assert len(unassigned) == 4


@pytest.mark.asyncio
async def test_explicit_backend_restart_persistence(tmp_path):
    """
    CRITICAL RESTART TEST:
    1. Start database backend with a persistent disk file.
    2. Register agent.
    3. Create job.
    4. Ingest artifact.
    5. Generate detection.
    6. Simulate full backend shutdown: dispose engine, clear in-memory singletons.
    7. Re-initialize new engine against the exact same database file on disk.
    8. Query all APIs and verify 100% data survival across backend restart.
    """
    db_file = tmp_path / "jocky_restart_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    # Phase A: First backend process lifecycle
    engine_1 = create_async_engine(db_url, connect_args={"check_same_thread": False})
    async with engine_1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory_1 = async_sessionmaker(
        bind=engine_1, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    agent_svc_1 = AgentService(session_factory=session_factory_1)
    job_svc_1 = JobService(session_factory=session_factory_1)
    detection_svc_1 = DetectionService(session_factory=session_factory_1)
    artifact_svc_1 = ArtifactService(
        detection_service=detection_svc_1, session_factory=session_factory_1
    )

    # 1. Register agent
    reg = await agent_svc_1.register_agent(
        AgentRegisterRequest(
            token="jocky-agent-insecure-dev-token",
            hostname="WIN11-SURVIVOR",
            os="windows",
            arch="amd64",
            agent_version="0.1.0",
        )
    )
    agent_id = reg.agent_id

    # 2. Create job
    job = await job_svc_1.create_and_dispatch_job(
        JobCreate(
            script_body="COLLECT autoruns;",
            target_agent_ids=[agent_id],
        )
    )
    job_id = job.job_id

    # 3. Ingest artifact
    await artifact_svc_1.ingest_artifacts(
        ArtifactSubmissionRequest(
            job_id=job_id,
            agent_id=agent_id,
            artifacts=[
                ArtifactItem(
                    id="art-survive-01",
                    type="autoruns",
                    target="registry",
                    data={"name": "Backdoor", "command": "C:\\Windows\\Temp\\evil.exe", "location": "HKCU\\Run"},
                )
            ],
        )
    )

    # Phase B: SIMULATE COMPLETE BACKEND SHUTDOWN & RESTART
    # Dispose all connections and clear in-memory state
    await engine_1.dispose()
    AgentService.reset_state()
    JobService.reset_state()
    ArtifactService.reset_state()
    DetectionService.reset_state()

    # Phase C: Second backend process lifecycle (reconnecting to same disk database)
    engine_2 = create_async_engine(db_url, connect_args={"check_same_thread": False})
    session_factory_2 = async_sessionmaker(
        bind=engine_2, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    agent_svc_2 = AgentService(session_factory=session_factory_2)
    job_svc_2 = JobService(session_factory=session_factory_2)
    detection_svc_2 = DetectionService(session_factory=session_factory_2)
    artifact_svc_2 = ArtifactService(
        detection_service=detection_svc_2, session_factory=session_factory_2
    )

    # 1. Verify Agent survived restart
    recovered_agent = await agent_svc_2.get_agent(agent_id)
    assert recovered_agent is not None
    assert recovered_agent.hostname == "WIN11-SURVIVOR"
    assert recovered_agent.os == "windows"
    assert recovered_agent.status == "online"

    # 2. Verify Job survived restart
    recovered_job = await job_svc_2.get_job(job_id)
    assert recovered_job is not None
    assert recovered_job.id == job_id
    assert agent_id in recovered_job.target_agents

    # 3. Verify Artifact survived restart
    recovered_art = await artifact_svc_2.get_artifact("art-survive-01")
    assert recovered_art is not None
    assert recovered_art.type == "autoruns"
    assert recovered_art.data["name"] == "Backdoor"

    # 4. Verify Detection survived restart
    recovered_dets = await detection_svc_2.list_detections(agent_id=agent_id)
    assert len(recovered_dets) >= 1
    assert recovered_dets[0].agent_id == agent_id
    assert recovered_dets[0].severity == "high"

    await engine_2.dispose()
