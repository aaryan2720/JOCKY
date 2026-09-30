import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient
from app.main import create_app
from app.services.artifact_service import ArtifactService
from app.services.job_service import JobService


@pytest.mark.asyncio
async def test_api_jobs_full_lifecycle():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Create job with script_body
        create_payload = {
            "script_body": "COLLECT autoruns; COLLECT users;",
            "target_agent_ids": ["agent-win-prod-01"],
            "target_tags": ["finance"],
        }
        resp = await client.post("/api/v1/jobs", json=create_payload)
        assert resp.status_code == 202
        job_data = resp.json()
        job_id = job_data["job_id"]
        assert job_id.startswith("job-")
        assert job_data["status"] == "queued"

        # List jobs
        list_resp = await client.get("/api/v1/jobs")
        assert list_resp.status_code == 200
        jobs = list_resp.json()
        assert any(j["id"] == job_id for j in jobs)

        # Get specific job
        get_resp = await client.get(f"/api/v1/jobs/{job_id}")
        assert get_resp.status_code == 200
        job_detail = get_resp.json()
        assert job_detail["id"] == job_id
        assert job_detail["status"] == "queued"
        assert job_detail["plan"] is not None
        assert "collectors" in job_detail["plan"]


@pytest.mark.asyncio
async def test_api_agents_retrieval():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        list_resp = await client.get("/api/v1/agents")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data["items"]) >= 1
        agent_id = data["items"][0]["id"]

        get_resp = await client.get(f"/api/v1/agents/{agent_id}")
        assert get_resp.status_code == 200
        agent = get_resp.json()
        assert agent["id"] == agent_id

        # 404 for missing agent
        missing_resp = await client.get("/api/v1/agents/agent-non-existent")
        assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_api_scripts_templates_and_validation():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Templates exist
        list_resp = await client.get("/api/v1/scripts")
        assert list_resp.status_code == 200
        scripts = list_resp.json()
        assert len(scripts) >= 3

        # Validate valid script
        val_resp = await client.post("/api/v1/scripts/validate", json={
            "body": "COLLECT processes; COLLECT connections;"
        })
        assert val_resp.status_code == 200
        val_data = val_resp.json()
        assert val_data["valid"] is True
        assert "processes" in val_data["estimated_artifacts"]
        assert "connections" in val_data["estimated_artifacts"]

        # Validate invalid syntax script
        invalid_resp = await client.post("/api/v1/scripts/validate", json={
            "body": "INVALID_VERB something syntax error;"
        })
        assert invalid_resp.status_code == 200
        inv_data = invalid_resp.json()
        assert inv_data["valid"] is False
        assert len(inv_data["errors"]) > 0


def test_websocket_live_feed_integration():
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/ws/jobs/job-ws-test-101") as websocket:
        # Initial greeting
        greeting = websocket.receive_json()
        assert greeting["event"] == "connected"
        assert greeting["job_id"] == "job-ws-test-101"

        # Ping pong
        websocket.send_text("ping")
        pong = websocket.receive_text()
        assert pong == "pong"
