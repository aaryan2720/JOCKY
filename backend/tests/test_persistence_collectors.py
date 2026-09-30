import pytest
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
from app.main import create_app
from app.detection.rules.suspicious_autorun import SuspiciousAutorunRule
from app.detection.rules.suspicious_user import SuspiciousUserRule
from app.detection.rules.flag_condition import FlagConditionRule
from app.services.detection_service import DetectionService
from app.services.artifact_service import ArtifactService


@pytest.fixture(autouse=True)
def reset_service_state():
    """Reset singleton services before each test."""
    DetectionService.get_instance().clear()
    ArtifactService.get_instance().clear()


# --- 1. AUTORUN-SUSP-001 Tests ---

def test_suspicious_autorun_temp_path_triggers_detection():
    rule = SuspiciousAutorunRule()
    artifacts = [
        {
            "id": "art-auto-1",
            "agent_id": "agent-win-01",
            "job_id": "job-p1",
            "type": "autorun",
            "data": {
                "name": "UpdaterService",
                "location": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "command": "C:\\Users\\Alice\\AppData\\Local\\Temp\\update.exe -run",
                "user": "Alice",
                "source": "registry",
                "enabled": True,
            },
        }
    ]

    detections = rule.evaluate(artifacts)
    assert len(detections) == 1
    det = detections[0]
    assert det.rule_id == "AUTORUN-SUSP-001"
    assert det.severity == "high"
    assert "volatile/suspicious directory" in det.description
    assert det.evidence[0].details["name"] == "UpdaterService"


def test_clean_autorun_program_files_no_detection():
    rule = SuspiciousAutorunRule()
    artifacts = [
        {
            "id": "art-auto-2",
            "agent_id": "agent-win-01",
            "job_id": "job-p1",
            "type": "autorun",
            "data": {
                "name": "RealtekAudio",
                "location": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "command": "C:\\Program Files\\Realtek\\Audio\\RtkAud.exe -s",
                "user": "SYSTEM",
                "source": "registry",
                "enabled": True,
            },
        }
    ]

    assert len(rule.evaluate(artifacts)) == 0


def test_linux_suspicious_autorun_tmp():
    rule = SuspiciousAutorunRule()
    artifacts = [
        {
            "id": "art-auto-linux",
            "agent_id": "agent-linux-01",
            "job_id": "job-p1",
            "type": "autorun",
            "data": {
                "name": "malicious_desktop",
                "location": "/etc/xdg/autostart/bad.desktop",
                "command": "/tmp/payload.sh",
                "user": "root",
                "source": "xdg_autostart",
                "enabled": True,
            },
        }
    ]

    detections = rule.evaluate(artifacts)
    assert len(detections) == 1
    assert detections[0].rule_id == "AUTORUN-SUSP-001"


# --- 2. USER-SUSP-001 Tests ---

def test_suspicious_user_active_guest_account():
    rule = SuspiciousUserRule()
    artifacts = [
        {
            "id": "art-usr-1",
            "agent_id": "agent-win-01",
            "job_id": "job-u1",
            "type": "user",
            "data": {
                "username": "Guest",
                "enabled": True,
                "account_type": "system",
                "description": "Built-in account for guest access",
            },
        }
    ]

    detections = rule.evaluate(artifacts)
    assert len(detections) == 1
    det = detections[0]
    assert det.rule_id == "USER-SUSP-001"
    assert det.severity == "medium"
    assert "Guest" in det.title


def test_disabled_guest_account_no_detection():
    rule = SuspiciousUserRule()
    artifacts = [
        {
            "id": "art-usr-2",
            "agent_id": "agent-win-01",
            "job_id": "job-u1",
            "type": "user",
            "data": {
                "username": "Guest",
                "enabled": False,
                "account_type": "system",
            },
        }
    ]

    assert len(rule.evaluate(artifacts)) == 0


def test_active_normal_user_no_detection():
    rule = SuspiciousUserRule()
    artifacts = [
        {
            "id": "art-usr-3",
            "agent_id": "agent-win-01",
            "job_id": "job-u1",
            "type": "user",
            "data": {
                "username": "sysadmin",
                "enabled": True,
                "account_type": "local",
            },
        }
    ]

    assert len(rule.evaluate(artifacts)) == 0


def test_suspicious_backdoor_account_name():
    rule = SuspiciousUserRule()
    artifacts = [
        {
            "id": "art-usr-4",
            "agent_id": "agent-linux-01",
            "job_id": "job-u1",
            "type": "user",
            "data": {
                "username": "backdoor_admin",
                "enabled": True,
                "account_type": "local",
                "description": "Hidden administrative account",
            },
        }
    ]

    detections = rule.evaluate(artifacts)
    assert len(detections) == 1
    assert "backdoor_admin" in detections[0].description


# --- 3. JOCKY Flag Conditions on New Collectors ---

def test_flag_condition_on_autorun_location():
    rule = FlagConditionRule(
        condition={"field": "location", "operator": "contains", "value": "RunOnce"},
        severity="medium",
        message="Flagged RunOnce persistence",
    )
    art1 = {
        "id": "1",
        "agent_id": "a1",
        "type": "autorun",
        "data": {"location": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce"},
    }
    art2 = {
        "id": "2",
        "agent_id": "a1",
        "type": "autorun",
        "data": {"location": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"},
    }
    results = rule.evaluate([art1, art2])
    assert len(results) == 1
    assert results[0].severity == "medium"


def test_flag_condition_on_scheduled_task_action():
    rule = FlagConditionRule(
        condition={"field": "action", "operator": "contains", "value": "powershell"},
        severity="high",
        message="Scheduled task executing PowerShell",
    )
    task1 = {
        "id": "t1",
        "agent_id": "a1",
        "type": "scheduled_task",
        "data": {"action": "powershell.exe -NoProfile -WindowStyle Hidden -Enc AAAA"},
    }
    task2 = {
        "id": "t2",
        "agent_id": "a1",
        "type": "scheduled_task",
        "data": {"action": "C:\\Windows\\system32\\usoclient.exe StartScan"},
    }
    results = rule.evaluate([task1, task2])
    assert len(results) == 1
    assert "Scheduled task executing PowerShell" in results[0].description


def test_flag_condition_on_user_account_shell():
    rule = FlagConditionRule(
        condition={"field": "shell", "operator": "endswith", "value": "/bin/bash"},
        severity="low",
    )
    u1 = {"id": "u1", "agent_id": "a1", "type": "user", "data": {"shell": "/bin/bash", "username": "root"}}
    u2 = {"id": "u2", "agent_id": "a1", "type": "user", "data": {"shell": "/usr/sbin/nologin", "username": "bin"}}
    results = rule.evaluate([u1, u2])
    assert len(results) == 1
    assert results[0].evidence[0].details["observed_value"] == "/bin/bash"


def test_flag_condition_on_session_logon_type():
    rule = FlagConditionRule(
        condition={"field": "logon_type", "operator": "eq", "value": "RDP"},
        severity="medium",
    )
    s1 = {"id": "s1", "agent_id": "a1", "type": "session", "data": {"logon_type": "RDP", "username": "remote_user"}}
    s2 = {"id": "s2", "agent_id": "a1", "type": "session", "data": {"logon_type": "Console", "username": "local_user"}}
    results = rule.evaluate([s1, s2])
    assert len(results) == 1
    assert results[0].evidence[0].details["observed_value"] == "RDP"


# --- 4. API Ingestion and Query Tests for New Artifacts ---

@pytest.mark.asyncio
async def test_api_ingest_and_query_persistence_and_identity_artifacts():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = [
            {
                "job_id": "job-persist-01",
                "agent_id": "agent-dfir-01",
                "type": "autorun",
                "data": {
                    "name": "BadStartup",
                    "location": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                    "command": "C:\\Temp\\dropper.exe",
                    "user": "Alice",
                    "source": "registry",
                    "enabled": True,
                },
            },
            {
                "job_id": "job-persist-01",
                "agent_id": "agent-dfir-01",
                "type": "scheduled_task",
                "data": {
                    "name": "DailyBackup",
                    "path": "\\DailyBackup",
                    "author": "ITAdmin",
                    "action": "C:\\Scripts\\backup.bat",
                    "trigger": "Daily",
                    "enabled": True,
                    "user": "SYSTEM",
                },
            },
            {
                "job_id": "job-persist-01",
                "agent_id": "agent-dfir-01",
                "type": "user",
                "data": {
                    "username": "Guest",
                    "enabled": True,
                    "account_type": "system",
                    "description": "Guest account",
                },
            },
            {
                "job_id": "job-persist-01",
                "agent_id": "agent-dfir-01",
                "type": "session",
                "data": {
                    "username": "admin",
                    "session_id": "2",
                    "state": "Active",
                    "logon_type": "RDP",
                    "client_name": "10.10.10.50",
                },
            },
        ]

        # Ingestion
        resp = await client.post("/api/v1/artifacts", json=payload)
        assert resp.status_code == 201
        ingested = resp.json()
        assert len(ingested) == 4

        # Query filter by type: autorun
        resp_auto = await client.get("/api/v1/artifacts?type=autorun")
        assert resp_auto.status_code == 200
        assert resp_auto.json()["total"] == 1
        assert resp_auto.json()["items"][0]["data"]["name"] == "BadStartup"

        # Query filter by type: scheduled_task
        resp_task = await client.get("/api/v1/artifacts?type=scheduled_task")
        assert resp_task.status_code == 200
        assert resp_task.json()["total"] == 1
        assert resp_task.json()["items"][0]["data"]["name"] == "DailyBackup"

        # Query filter by type: user
        resp_usr = await client.get("/api/v1/artifacts?type=user")
        assert resp_usr.status_code == 200
        assert resp_usr.json()["total"] == 1

        # Query filter by type: session
        resp_sess = await client.get("/api/v1/artifacts?type=session")
        assert resp_sess.status_code == 200
        assert resp_sess.json()["total"] == 1

        # Verify automated detection triggered by ingested autorun and user
        resp_det = await client.get("/api/v1/detections")
        assert resp_det.status_code == 200
        det_items = resp_det.json()["items"]
        rule_ids = [d["rule_id"] for d in det_items]
        assert "AUTORUN-SUSP-001" in rule_ids
        assert "USER-SUSP-001" in rule_ids
