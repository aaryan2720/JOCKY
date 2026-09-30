import pytest
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
from app.main import create_app
from app.services.detection_service import DetectionService
from app.services.artifact_service import ArtifactService


@pytest.fixture(autouse=True)
def reset_service_state():
    """Reset singleton service stores before each test."""
    DetectionService.get_instance().clear()
    ArtifactService.get_instance().clear()


@pytest.mark.asyncio
async def test_detection_api_endpoints_and_filtering():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Ingest artifacts that trigger PROC-UNSIGNED-001
        payload = [
            {
                "job_id": "job-api-1",
                "agent_id": "agent-api-1",
                "type": "process",
                "data": {
                    "pid": 3001,
                    "name": "suspicious.exe",
                    "path": "C:\\Windows\\Temp\\suspicious.exe",
                    "signature_status": "unsigned",
                },
            },
            {
                "job_id": "job-api-2",
                "agent_id": "agent-api-2",
                "type": "process",
                "data": {
                    "pid": 3002,
                    "name": "powershell.exe",
                    "parent_name": "wmiprvse.exe",
                    "signature_status": "signed",
                },
            },
        ]

        resp_ingest = await client.post("/api/v1/artifacts", json=payload)
        assert resp_ingest.status_code == 201
        ingested_items = resp_ingest.json()
        assert len(ingested_items) == 2

        # 2. List all detections
        resp_det = await client.get("/api/v1/detections")
        assert resp_det.status_code == 200
        data = resp_det.json()
        assert data["total"] >= 2
        items = data["items"]

        # 3. Test filtering by agent_id
        resp_agent1 = await client.get("/api/v1/detections?agent_id=agent-api-1")
        assert resp_agent1.status_code == 200
        agent1_data = resp_agent1.json()
        assert agent1_data["total"] == 1
        assert agent1_data["items"][0]["agent_id"] == "agent-api-1"
        assert agent1_data["items"][0]["rule_id"] == "PROC-UNSIGNED-001"

        # 4. Test filtering by rule_id
        resp_parent = await client.get("/api/v1/detections?rule_id=PROC-PARENT-001")
        assert resp_parent.status_code == 200
        parent_data = resp_parent.json()
        assert parent_data["total"] == 1
        assert parent_data["items"][0]["rule_id"] == "PROC-PARENT-001"

        # 5. Test filtering by severity
        resp_sev = await client.get("/api/v1/detections?severity=high")
        assert resp_sev.status_code == 200
        sev_data = resp_sev.json()
        assert all(d["severity"] == "high" for d in sev_data["items"])

        # 6. Test GET /api/v1/detections/{id}
        first_det_id = items[0]["id"]
        resp_single = await client.get(f"/api/v1/detections/{first_det_id}")
        assert resp_single.status_code == 200
        single_det = resp_single.json()
        assert single_det["id"] == first_det_id
        assert "evidence" in single_det
        assert len(single_det["evidence"]) >= 1

        # 7. Test GET /api/v1/detections/{non_existent} -> 404
        resp_404 = await client.get("/api/v1/detections/det-nonexistent-12345")
        assert resp_404.status_code == 404


@pytest.mark.asyncio
async def test_artifact_ingestion_preserves_evidence_on_detection_error(monkeypatch):
    """Verifies that an unexpected detection engine error does not abort artifact storage."""
    app = create_app()
    transport = ASGITransport(app=app)

    det_service = DetectionService.get_instance()

    # Intentionally force detection service to raise an exception
    async def faulty_process(*args, **kwargs):
        raise RuntimeError("Simulated transient detection engine failure")

    monkeypatch.setattr(det_service, "process_artifacts", faulty_process)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        art_payload = {
            "job_id": "job-resilience",
            "agent_id": "agent-resilience",
            "type": "process",
            "data": {"pid": 777, "name": "critical_evidence.exe"},
        }

        # Ingestion must succeed (201 Created) despite detection engine failure
        resp = await client.post("/api/v1/artifacts", json=art_payload)
        assert resp.status_code == 201
        created = resp.json()
        assert len(created) == 1
        art_id = created[0]["id"]

        # Artifact must be queryable in database/store
        resp_get = await client.get(f"/api/v1/artifacts/{art_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["data"]["name"] == "critical_evidence.exe"
