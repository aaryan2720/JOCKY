import pytest
from datetime import datetime, timezone, timedelta
from app.detection.rules.unsigned_process import UnsignedProcessRule
from app.detection.rules.process_network import UnsignedProcessNetworkRule
from app.detection.rules.parent_child import SuspiciousParentChildRule
from app.detection.rules.flag_condition import (
    FlagConditionRule,
    evaluate_condition_predicate,
)
from app.detection.engine import DetectionEngine, compute_dedup_key
from app.services.detection_service import DetectionService
from app.services.artifact_service import ArtifactService


# --- 1. Unsigned Process Rule (PROC-UNSIGNED-001) Tests ---

def test_unsigned_process_triggers_detection():
    rule = UnsignedProcessRule()
    artifacts = [
        {
            "id": "art-proc-1",
            "agent_id": "agent-win-1",
            "job_id": "job-101",
            "type": "process",
            "data": {
                "pid": 4812,
                "name": "mimikatz.exe",
                "path": "C:\\Temp\\mimikatz.exe",
                "signature_status": "unsigned",
            },
        }
    ]
    detections = rule.evaluate(artifacts)
    assert len(detections) == 1
    det = detections[0]
    assert det.rule_id == "PROC-UNSIGNED-001"
    assert det.severity == "high"
    assert det.agent_id == "agent-win-1"
    assert det.job_id == "job-101"
    assert len(det.evidence) == 1
    assert det.evidence[0].artifact_id == "art-proc-1"
    assert det.evidence[0].details["signature_status"] == "unsigned"
    assert "reports an unsigned executable" in det.description


def test_signed_process_no_detection():
    rule = UnsignedProcessRule()
    artifacts = [
        {
            "id": "art-proc-2",
            "agent_id": "agent-win-1",
            "job_id": "job-101",
            "type": "process",
            "data": {
                "pid": 1004,
                "name": "svchost.exe",
                "path": "C:\\Windows\\System32\\svchost.exe",
                "signature_status": "signed",
            },
        }
    ]
    detections = rule.evaluate(artifacts)
    assert len(detections) == 0


def test_linux_unsupported_signature_no_detection():
    rule = UnsignedProcessRule()
    artifacts = [
        {
            "id": "art-proc-linux",
            "agent_id": "agent-linux-1",
            "job_id": "job-102",
            "type": "process",
            "data": {
                "pid": 500,
                "name": "systemd",
                "path": "/usr/lib/systemd/systemd",
                "signature_status": "unsupported",
            },
        }
    ]
    detections = rule.evaluate(artifacts)
    assert len(detections) == 0


def test_missing_signature_status_no_detection():
    rule = UnsignedProcessRule()
    artifacts = [
        {
            "id": "art-proc-3",
            "agent_id": "agent-win-1",
            "job_id": "job-101",
            "type": "process",
            "data": {
                "pid": 2048,
                "name": "calc.exe",
            },
        }
    ]
    detections = rule.evaluate(artifacts)
    assert len(detections) == 0


# --- 2. Process / Network Correlation Rule (PROC-NET-001) Tests ---

def test_process_network_correlation_success():
    rule = UnsignedProcessNetworkRule(correlation_window_seconds=300)
    now = datetime.now(timezone.utc)
    artifacts = [
        {
            "id": "art-proc-1",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "process",
            "collected_at": now,
            "data": {
                "pid": 4812,
                "name": "nc.exe",
                "signature_status": "unsigned",
            },
        },
        {
            "id": "art-net-1",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "network_connection",
            "collected_at": now + timedelta(seconds=10),
            "data": {
                "pid": 4812,
                "dest_ip": "10.0.0.5",
                "dest_port": 4444,
                "protocol": "TCP",
            },
        },
    ]
    detections = rule.evaluate(artifacts)
    assert len(detections) == 1
    det = detections[0]
    assert det.rule_id == "PROC-NET-001"
    assert det.severity == "high"
    assert len(det.evidence) == 2
    ev_types = [e.type for e in det.evidence]
    assert "process" in ev_types
    assert "network_connection" in ev_types
    assert "10.0.0.5:4444" in det.description
    assert "PID 4812" in det.description


def test_process_network_signed_process_no_detection():
    rule = UnsignedProcessNetworkRule(correlation_window_seconds=300)
    now = datetime.now(timezone.utc)
    artifacts = [
        {
            "id": "art-proc-signed",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "process",
            "collected_at": now,
            "data": {
                "pid": 4812,
                "name": "chrome.exe",
                "signature_status": "signed",
            },
        },
        {
            "id": "art-net-1",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "network",
            "collected_at": now,
            "data": {
                "pid": 4812,
                "dest_ip": "142.250.190.46",
                "dest_port": 443,
            },
        },
    ]
    assert len(rule.evaluate(artifacts)) == 0


def test_process_network_different_pid_no_detection():
    rule = UnsignedProcessNetworkRule(correlation_window_seconds=300)
    now = datetime.now(timezone.utc)
    artifacts = [
        {
            "id": "art-proc-1",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "process",
            "collected_at": now,
            "data": {"pid": 1111, "name": "bad.exe", "signature_status": "unsigned"},
        },
        {
            "id": "art-net-1",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "network",
            "collected_at": now,
            "data": {"pid": 2222, "dest_ip": "10.0.0.5", "dest_port": 80},
        },
    ]
    assert len(rule.evaluate(artifacts)) == 0


def test_process_network_different_agent_no_detection():
    rule = UnsignedProcessNetworkRule(correlation_window_seconds=300)
    now = datetime.now(timezone.utc)
    artifacts = [
        {
            "id": "art-proc-1",
            "agent_id": "agent-A",
            "job_id": "job-1",
            "type": "process",
            "collected_at": now,
            "data": {"pid": 1234, "name": "bad.exe", "signature_status": "unsigned"},
        },
        {
            "id": "art-net-1",
            "agent_id": "agent-B",
            "job_id": "job-1",
            "type": "network",
            "collected_at": now,
            "data": {"pid": 1234, "dest_ip": "10.0.0.5", "dest_port": 80},
        },
    ]
    assert len(rule.evaluate(artifacts)) == 0


def test_process_network_outside_time_window_no_detection():
    rule = UnsignedProcessNetworkRule(correlation_window_seconds=300)
    t1 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 30, 10, 10, 0, tzinfo=timezone.utc)  # 10 minutes later > 300s
    artifacts = [
        {
            "id": "art-proc-1",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "process",
            "collected_at": t1,
            "data": {"pid": 1234, "name": "bad.exe", "signature_status": "unsigned"},
        },
        {
            "id": "art-net-1",
            "agent_id": "agent-01",
            "job_id": "job-1",
            "type": "network",
            "collected_at": t2,
            "data": {"pid": 1234, "dest_ip": "10.0.0.5", "dest_port": 80},
        },
    ]
    assert len(rule.evaluate(artifacts)) == 0


# --- 3. Suspicious Parent / Child Rule (PROC-PARENT-001) Tests ---

def test_suspicious_parent_child_match():
    rule = SuspiciousParentChildRule()
    artifacts = [
        {
            "id": "art-pc-1",
            "agent_id": "agent-win-1",
            "job_id": "job-001",
            "type": "process",
            "data": {
                "pid": 4920,
                "ppid": 1024,
                "name": "powershell.exe",
                "parent_name": "wmiprvse.exe",
                "cmdline": "powershell.exe -enc AAAA...",
            },
        }
    ]
    detections = rule.evaluate(artifacts)
    assert len(detections) == 1
    det = detections[0]
    assert det.rule_id == "PROC-PARENT-001"
    assert "wmiprvse.exe" in det.description
    assert "powershell.exe" in det.description
    assert det.severity == "high"


def test_normal_parent_child_no_detection():
    rule = SuspiciousParentChildRule()
    artifacts = [
        {
            "id": "art-pc-2",
            "agent_id": "agent-win-1",
            "job_id": "job-001",
            "type": "process",
            "data": {
                "pid": 6000,
                "ppid": 1200,
                "name": "notepad.exe",
                "parent_name": "explorer.exe",
            },
        }
    ]
    detections = rule.evaluate(artifacts)
    assert len(detections) == 0


# --- 4. JOCKY Flag Evaluation Tests ---

def test_flag_evaluation_supported_operators():
    # Test equality
    rule_eq = FlagConditionRule(
        condition={"field": "signed", "operator": "eq", "value": False},
        severity="high",
        message="Flagged unsigned process",
    )
    art1 = {"id": "1", "agent_id": "a1", "job_id": "j1", "type": "process", "data": {"signature_status": "unsigned"}}
    art2 = {"id": "2", "agent_id": "a1", "job_id": "j1", "type": "process", "data": {"signature_status": "signed"}}
    assert len(rule_eq.evaluate([art1, art2])) == 1

    # Test contains
    rule_contains = FlagConditionRule(
        condition={"field": "name", "operator": "contains", "value": "power"},
        severity="medium",
    )
    art_ps = {"id": "3", "agent_id": "a1", "job_id": "j1", "type": "process", "data": {"name": "PowerShell.exe"}}
    assert len(rule_contains.evaluate([art_ps])) == 1

    # Test numeric comparison
    rule_gt = FlagConditionRule(
        condition={"field": "dest_port", "operator": ">", "value": 1024},
        severity="low",
    )
    art_net = {"id": "4", "agent_id": "a1", "job_id": "j1", "type": "network", "data": {"dest_port": 4444}}
    assert len(rule_gt.evaluate([art_net])) == 1


def test_flag_evaluation_unsupported_operator():
    rule = FlagConditionRule(
        condition={"field": "name", "operator": "eval", "value": "calc"}
    )
    with pytest.raises(ValueError, match="Unsupported condition operator"):
        rule.evaluate([{"id": "1", "agent_id": "a1", "data": {"name": "test"}}])


def test_flag_evaluation_unsupported_field():
    rule = FlagConditionRule(
        condition={"field": "dangerous_secret_key", "operator": "eq", "value": "x"}
    )
    with pytest.raises(ValueError, match="Unsupported flag condition field"):
        rule.evaluate([{"id": "1", "agent_id": "a1", "data": {"dangerous_secret_key": "x"}}])


def test_flag_evaluation_malformed_condition():
    rule_missing_field = FlagConditionRule(condition={"operator": "eq", "value": "x"})
    with pytest.raises(ValueError, match="missing 'field'"):
        rule_missing_field.evaluate([{"id": "1", "data": {}}])


# --- 5. Deduplication Tests ---

@pytest.mark.asyncio
async def test_detection_deduplication():
    service = DetectionService()
    service.clear()

    artifacts = [
        {
            "id": "art-dup-1",
            "agent_id": "agent-dup",
            "job_id": "job-dup",
            "type": "process",
            "data": {
                "pid": 9999,
                "name": "malicious.exe",
                "signature_status": "unsigned",
            },
        }
    ]

    # First evaluation generates detection
    dets_1 = await service.process_artifacts(artifacts)
    assert len(dets_1) == 1

    # Second evaluation with the exact same batch produces 0 new detections (deduplicated)
    dets_2 = await service.process_artifacts(artifacts)
    assert len(dets_2) == 0

    # Total stored detections remains 1
    all_dets = await service.list_detections(agent_id="agent-dup")
    assert len(all_dets) == 1


# --- 6. Extended Operator and Plan Execution Tests ---

def test_flag_evaluation_additional_operators():
    # Test neq
    rule_neq = FlagConditionRule(
        condition={"field": "name", "operator": "neq", "value": "system"},
        severity="low",
    )
    art = {"id": "1", "agent_id": "a1", "job_id": "j1", "type": "process", "data": {"name": "malware.exe"}}
    assert len(rule_neq.evaluate([art])) == 1

    # Test startswith
    rule_start = FlagConditionRule(
        condition={"field": "path", "operator": "startswith", "value": "C:\\Temp"},
        severity="medium",
    )
    art_temp = {"id": "2", "agent_id": "a1", "job_id": "j1", "type": "process", "data": {"path": "C:\\Temp\\dropper.exe"}}
    assert len(rule_start.evaluate([art_temp])) == 1

    # Test endswith
    rule_end = FlagConditionRule(
        condition={"field": "name", "operator": "endswith", "value": ".scr"},
        severity="high",
    )
    art_scr = {"id": "3", "agent_id": "a1", "job_id": "j1", "type": "process", "data": {"name": "invoice.scr"}}
    assert len(rule_end.evaluate([art_scr])) == 1

    # Test regex / matches
    rule_regex = FlagConditionRule(
        condition={"field": "cmdline", "operator": "regex", "value": r"-enc(odedcommand)?\s+[a-zA-Z0-9+/=]{10,}"},
        severity="critical",
    )
    art_enc = {
        "id": "4",
        "agent_id": "a1",
        "job_id": "j1",
        "type": "process",
        "data": {"cmdline": "powershell.exe -enc SQBFAFgAKABOAGUAdwAtAE8AYgBqAGUAYwB0AA=="},
    }
    assert len(rule_regex.evaluate([art_enc])) == 1

    # Test invalid regex
    rule_bad_regex = FlagConditionRule(
        condition={"field": "cmdline", "operator": "regex", "value": "["}
    )
    with pytest.raises(ValueError, match="Invalid regular expression"):
        rule_bad_regex.evaluate([art_enc])


def test_flag_evaluation_numeric_inequalities():
    # Test lte
    assert evaluate_condition_predicate(10, "<=", 10) is True
    assert evaluate_condition_predicate(11, "<=", 10) is False

    # Test lt
    assert evaluate_condition_predicate(9, "<", 10) is True
    assert evaluate_condition_predicate(10, "<", 10) is False

    # Test gte
    assert evaluate_condition_predicate(10, ">=", 10) is True
    assert evaluate_condition_predicate(9, ">=", 10) is False


def test_detection_engine_with_plan_flags():
    engine = DetectionEngine()
    plan = {
        "plan_version": "1.0",
        "checks": [
            {
                "operation": "flag",
                "condition": {"field": "dest_port", "operator": "eq", "value": 4444},
                "severity": "critical",
                "message": "Metasploit default listener port matched",
            }
        ],
    }

    artifacts = [
        {
            "id": "art-net-c2",
            "agent_id": "agent-c2",
            "job_id": "job-c2",
            "type": "network",
            "data": {
                "pid": 5555,
                "dest_ip": "198.51.100.23",
                "dest_port": 4444,
            },
        }
    ]

    results = engine.evaluate_artifacts(artifacts, plan=plan)
    assert len(results) >= 1
    det, dedup_key = results[0]
    assert det.severity == "critical"
    assert "Metasploit default listener" in det.description
    assert compute_dedup_key(det.rule_id, det.agent_id, det.job_id, ["art-net-c2"]) == dedup_key

