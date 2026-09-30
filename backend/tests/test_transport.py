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
