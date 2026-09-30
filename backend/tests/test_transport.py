import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.agent_service import AgentService
from app.services.job_service import JobService
from app.services.artifact_service import ArtifactService


@pytest.fixture(autouse=True)
def reset_service_state():
    AgentService.reset_state()
    JobService.reset_state()
    ArtifactService.reset_state()


@pytest.mark.asyncio
async def test_agent_registration_and_heartbeat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register agent
        reg_payload = {
            "token": "jocky-agent-insecure-dev-token",
            "hostname": "ENDPOINT-WIN-01",
            "os": "windows",
            "arch": "amd64",
            "agent_version": "0.1.0",
        }
        res = await client.post("/api/v1/agents/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["agent_id"] == "agent-endpoint-win-01-windows"
        assert data["status"] == "enrolled"
        assert data["heartbeat_interval_seconds"] == 5

        # 2. List agents
        list_res = await client.get("/api/v1/agents")
        assert list_res.status_code == 200
        agents_data = list_res.json()
        assert agents_data["total"] == 1
        assert agents_data["items"][0]["id"] == "agent-endpoint-win-01-windows"
        assert agents_data["items"][0]["status"] == "online"

        # 3. Heartbeat
        hb_res = await client.post(
            f"/api/v1/agents/{data['agent_id']}/heartbeat",
            json={"status": "online"},
        )
        assert hb_res.status_code == 200
        assert hb_res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_job_dispatch_with_dsl_and_agent_polling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        agent_id = "agent-test-host-linux"
        # Register agent first
        await client.post(
            "/api/v1/agents/register",
            json={
                "token": "test-token",
                "hostname": "test-host",
                "os": "linux",
                "arch": "amd64",
                "agent_version": "0.1.0",
            },
        )

        # Dispatch job with JOCKY DSL script body
        jocky_script = "scan processes\nwhere signed == false"
        job_res = await client.post(
            "/api/v1/jobs",
            json={
                "script_body": jocky_script,
                "target_agent_ids": [agent_id],
            },
        )
        assert job_res.status_code == 202
        job_data = job_res.json()
        job_id = job_data["job_id"]
        assert job_data["status"] == "queued"
        assert job_data["agent_count"] == 1

        # Poll job from agent
        poll_res = await client.get(f"/api/v1/agents/{agent_id}/jobs/poll")
        assert poll_res.status_code == 200
        polled = poll_res.json()
        assert polled["job_id"] == job_id
        assert polled["plan"] is not None
        assert polled["plan"]["version"] == "1"
        assert polled["plan"]["statements"][0]["operation"] == "scan"
        assert polled["plan"]["statements"][0]["target"] == "processes"

        # Subsequent poll should return empty
        empty_poll = await client.get(f"/api/v1/agents/{agent_id}/jobs/poll")
        assert empty_poll.status_code == 200
        assert empty_poll.json()["job_id"] is None


@pytest.mark.asyncio
async def test_artifact_submission_and_querying():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        submission = {
            "job_id": "job-12345",
            "agent_id": "agent-host1-windows",
            "artifacts": [
                {
                    "type": "process",
                    "target": "processes",
                    "data": {
                        "pid": 1337,
                        "name": "suspicious.exe",
                        "path": "C:\\Windows\\Temp\\suspicious.exe",
                    },
                    "metadata": {"os": "windows"},
                },
                {
                    "type": "network_connection",
                    "target": "connections",
                    "data": {
                        "protocol": "tcp",
                        "local_port": 4444,
                        "state": "LISTENING",
                    },
                    "metadata": {"os": "windows"},
                },
            ],
        }

        # Submit artifacts
        sub_res = await client.post("/api/v1/artifacts", json=submission)
        assert sub_res.status_code == 201
        assert sub_res.json()["status"] == "ok"
        assert sub_res.json()["ingested"] == 2

        # Query all artifacts
        list_res = await client.get("/api/v1/artifacts")
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 2

        # Query filtered by type
        filter_res = await client.get("/api/v1/artifacts?type=process")
        assert filter_res.status_code == 200
        assert filter_res.json()["total"] == 1
        assert filter_res.json()["items"][0]["data"]["pid"] == 1337


@pytest.mark.asyncio
async def test_job_dispatch_file_hash_and_artifact_ingestion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        agent_id = "agent-forensic-win-01"
        await client.post(
            "/api/v1/agents/register",
            json={
                "token": "test-token",
                "hostname": "forensic-win-01",
                "os": "windows",
                "arch": "amd64",
                "agent_version": "0.1.0",
            },
        )

        # Dispatch JOCKY hash job
        dsl_script = 'hash files in "%TEMP%" check against reputation'
        job_res = await client.post(
            "/api/v1/jobs",
            json={
                "script_body": dsl_script,
                "target_agent_ids": [agent_id],
            },
        )
        assert job_res.status_code == 202
        job_id = job_res.json()["job_id"]

        # Poll job
        poll_res = await client.get(f"/api/v1/agents/{agent_id}/jobs/poll")
        assert poll_res.status_code == 200
        polled = poll_res.json()
        assert polled["job_id"] == job_id
        stmt = polled["plan"]["statements"][0]
        assert stmt["operation"] == "hash"
        assert stmt["target"] == "files"
        assert stmt["path"] == "%TEMP%"

        # Submit simulated file artifact with sha256
        submission = {
            "job_id": job_id,
            "agent_id": agent_id,
            "artifacts": [
                {
                    "type": "file",
                    "target": "files",
                    "data": {
                        "path": "C:\\Users\\test\\AppData\\Local\\Temp\\sample.exe",
                        "name": "sample.exe",
                        "size": 1024,
                        "is_dir": False,
                        "extension": ".exe",
                        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        "modified_at": "2026-09-30T10:00:00Z",
                    },
                }
            ],
        }
        sub_res = await client.post("/api/v1/artifacts", json=submission)
        assert sub_res.status_code == 201

        # Query file artifact
        get_res = await client.get("/api/v1/artifacts?type=file")
        assert get_res.status_code == 200
        assert get_res.json()["total"] == 1
        art = get_res.json()["items"][0]
        assert art["data"]["sha256"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert art["data"]["name"] == "sample.exe"


@pytest.mark.asyncio
async def test_job_dispatch_services_and_drivers_ingestion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        agent_id = "agent-srv-drv-01"
        await client.post(
            "/api/v1/agents/register",
            json={
                "token": "test-token",
                "hostname": "srv-drv-host",
                "os": "windows",
                "arch": "amd64",
                "agent_version": "0.1.0",
            },
        )

        # Dispatch JOCKY collect services, drivers job
        dsl_script = "collect services, drivers\nreport to server"
        job_res = await client.post(
            "/api/v1/jobs",
            json={
                "script_body": dsl_script,
                "target_agent_ids": [agent_id],
            },
        )
        assert job_res.status_code == 202
        job_id = job_res.json()["job_id"]

        # Poll job
        poll_res = await client.get(f"/api/v1/agents/{agent_id}/jobs/poll")
        assert poll_res.status_code == 200
        polled = poll_res.json()
        assert polled["job_id"] == job_id
        stmt = polled["plan"]["statements"][0]
        assert stmt["operation"] == "collect"
        assert stmt["targets"] == ["services", "drivers"]

        # Ingest both service and driver artifacts
        submission = {
            "job_id": job_id,
            "agent_id": agent_id,
            "artifacts": [
                {
                    "type": "service",
                    "target": "services",
                    "data": {
                        "name": "wuauserv",
                        "display_name": "Windows Update",
                        "status": "running",
                        "start_type": "auto",
                        "path": "C:\\Windows\\system32\\svchost.exe -k netsvcs -p",
                        "user": "LocalSystem",
                        "source": "windows_service",
                    },
                },
                {
                    "type": "driver",
                    "target": "drivers",
                    "data": {
                        "name": "tcpip",
                        "display_name": "TCP/IP Protocol Driver",
                        "state": "Running",
                        "path": "C:\\Windows\\system32\\drivers\\tcpip.sys",
                        "type": "Kernel",
                        "source": "driverquery",
                    },
                },
            ],
        }
        sub_res = await client.post("/api/v1/artifacts", json=submission)
        assert sub_res.status_code == 201
        assert sub_res.json()["ingested"] == 2

        # Query services
        svc_res = await client.get("/api/v1/artifacts?type=service")
        assert svc_res.status_code == 200
        assert svc_res.json()["total"] == 1
        assert svc_res.json()["items"][0]["data"]["name"] == "wuauserv"

        # Query drivers
        drv_res = await client.get("/api/v1/artifacts?type=driver")
        assert drv_res.status_code == 200
        assert drv_res.json()["total"] == 1
        assert drv_res.json()["items"][0]["data"]["name"] == "tcpip"


@pytest.mark.asyncio
async def test_job_dispatch_event_logs_ingestion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        agent_id = "agent-event-logs-01"
        await client.post(
            "/api/v1/agents/register",
            json={
                "token": "test-token",
                "hostname": "event-log-host",
                "os": "windows",
                "arch": "amd64",
                "agent_version": "0.1.0",
            },
        )

        # Dispatch JOCKY collect event_logs job
        dsl_script = "collect event_logs\nreport to server"
        job_res = await client.post(
            "/api/v1/jobs",
            json={
                "script_body": dsl_script,
                "target_agent_ids": [agent_id],
            },
        )
        assert job_res.status_code == 202
        job_id = job_res.json()["job_id"]

        # Poll job
        poll_res = await client.get(f"/api/v1/agents/{agent_id}/jobs/poll")
        assert poll_res.status_code == 200
        polled = poll_res.json()
        assert polled["job_id"] == job_id
        stmt = polled["plan"]["statements"][0]
        assert stmt["operation"] == "collect"
        assert stmt["targets"] == ["event_logs"]

        # Ingest normalized event artifact
        submission = {
            "job_id": job_id,
            "agent_id": agent_id,
            "artifacts": [
                {
                    "type": "event",
                    "target": "event_logs",
                    "data": {
                        "channel": "System",
                        "event_id": 7036,
                        "provider": "Service Control Manager",
                        "level": "Information",
                        "timestamp": "2026-09-30T10:00:00Z",
                        "record_id": 14523,
                        "computer": "WORKSTATION-01",
                        "message": "The Windows Update service entered the running state.",
                        "source": "wevtutil",
                    },
                }
            ],
        }
        sub_res = await client.post("/api/v1/artifacts", json=submission)
        assert sub_res.status_code == 201
        assert sub_res.json()["ingested"] == 1

        # Query events
        evt_res = await client.get("/api/v1/artifacts?type=event")
        assert evt_res.status_code == 200
        assert evt_res.json()["total"] == 1
        art = evt_res.json()["items"][0]
        assert art["data"]["event_id"] == 7036
        assert art["data"]["channel"] == "System"
        assert art["data"]["provider"] == "Service Control Manager"
