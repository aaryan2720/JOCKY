# JOCKY Developer Documentation & Implementation Truth

## 1. Last Completed Task
**Phase 5 — Adversary Detection & Correlation Engine**

---

## 2. Current Architecture & State

### End-to-End Forensic & Detection Flow
```text
JOCKY DSL Script / Flag Condition
   ↓
FastAPI Compiles Execution Plan
   ↓
Job Queue & Agent Polling
   ↓
Go Forensic Agent Plan Validation
   ↓
Read-Only Forensic OS Collectors (Processes, Connections)
   ↓
Artifact Submission (POST /api/v1/artifacts)
   ↓
Artifact Persistence & Preservation
   ↓
Detection Engine Evaluation (Heuristics + Flag Rules)
   ↓
Deterministic Deduplication
   ↓
Detection Persistence (GET /api/v1/detections)
```

### Implemented Capabilities

1. **Adversary Detection Engine (`backend/app/detection/`)**:
   - **`DetectionRule` Protocol**: Deterministic, testable, explainable, and independently identifiable rule interface.
   - **`PROC-UNSIGNED-001`**: Unsigned process detection (triggers when `artifact.type == "process"` and `signature_status == "unsigned"`; ignores signed binaries and unsupported OS signatures).
   - **`PROC-NET-001`**: Correlates unsigned process executables with active network connections originating from the same PID on the same agent within a configurable time window (default: 300 seconds).
   - **`PROC-PARENT-001`**: Suspicious process lineage / parent-child detection using configuration loaded from `rules/suspicious_parent_child.json`.
   - **`FLAG-DYNAMIC-001` (`FlagConditionRule`)**: Safe, deterministic evaluation of JOCKY DSL `flag` statement conditions from compiled execution plans. Supports operators (`eq`, `neq`, `contains`, `in`, `gt`, `gte`, `lt`, `lte`, `startswith`, `endswith`, `matches`/`regex`) across forensic fields (`signed`, `name`, `pid`, `ppid`, `path`, `cmdline`, `dest_ip`, `dest_port`, `hash`, `username`, `status`) without `eval()`.
   - **Deduplication Engine**: Deterministic SHA-256 deduplication hashing using `rule_id`, `agent_id`, `job_id`, and sorted evidence artifact IDs to prevent duplicate alert generation on re-processing.

2. **Service Layer (`backend/app/services/`)**:
   - **`DetectionService`**: Coordinates rule evaluation, deduplication, and querying of correlated threat alerts.
   - **`ArtifactService`**: Persists incoming forensic artifacts and triggers the detection engine in a non-fatal guarded try/except block to ensure forensic evidence is never lost or corrupted on rule failure.
   - **`AgentService`**: Fleet registration and enrollment.
   - **`JobService`**: Forensic job creation and plan dispatch.

3. **REST API Endpoints (`backend/app/api/routes/`)**:
   - `GET /health`: Health check.
   - `GET /api/v1/agents`: List fleet agents.
   - `POST /api/v1/agents/register`: Agent enrollment.
   - `POST /api/v1/artifacts`: Ingest artifacts and run detection pipeline.
   - `GET /api/v1/artifacts`: Query forensic artifacts with `job_id`, `agent_id`, `type` filters.
   - `GET /api/v1/artifacts/{id}`: Retrieve single artifact.
   - `GET /api/v1/detections`: Query detections with `agent_id`, `job_id`, `severity`, `status`, `rule_id` filters.
   - `GET /api/v1/detections/{id}`: Retrieve single detection with full structured evidence references.

4. **Agent Runtime (`agent/`)**:
   - Go agent runtime, enrollment client, execution engine, and read-only OS collectors (`processes`, `connections`).

---

## 3. Test & Build Verification

- **Python Test Suite**:
  - `python -m pytest -v` -> **25/25 passed** in 1.60s (Rules, Correlation, Flag conditions, Operators, Deduplication, API endpoints, Resilience).
- **Go Test Suite & Build**:
  - `go test -v -count=1 ./...` -> **PASS**
  - `go build ./...` -> **Binary build successful**.

---

## 4. Current API & Data Contracts

### Detection Schema
```json
{
  "id": "det-a7c83f9e1201",
  "agent_id": "agent-df84b2c1",
  "job_id": "job-78a9c2",
  "rule_id": "PROC-NET-001",
  "severity": "high",
  "title": "Unsigned process with active network connection",
  "description": "Process PID 4812 (mimikatz.exe) reported unsigned and was associated with TCP connection 10.0.0.5:4444.",
  "status": "open",
  "created_at": "2026-09-30T09:40:02Z",
  "evidence": [
    {
      "artifact_id": "art-19f8a3c42b10",
      "type": "process",
      "details": {
        "pid": 4812,
        "name": "mimikatz.exe",
        "path": "C:\\Temp\\mimikatz.exe",
        "signature_status": "unsigned"
      }
    },
    {
      "artifact_id": "art-98d7b1a20c34",
      "type": "network_connection",
      "details": {
        "pid": 4812,
        "dest_ip": "10.0.0.5",
        "dest_port": 4444,
        "protocol": "TCP",
        "state": "ESTABLISHED"
      }
    }
  ]
}
```

---

## 5. Known Limitations

1. **YARA & Sigma Engines**: Full YARA binary scanning and Sigma YAML translation engines are not yet implemented in the agent/backend (deferred by design to keep Phase 5 small, deterministic, and explainable).
2. **Rule Set Scope**: Only the initial deterministic heuristic rules (`PROC-UNSIGNED-001`, `PROC-NET-001`, `PROC-PARENT-001`, `FLAG-DYNAMIC-001`) are implemented.
3. **Placeholder Collectors**: The remaining eight forensic collectors (`files`, `drivers`, `services`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `event_logs`) remain placeholder stubs.
4. **Dashboard UI**: The frontend React dashboard currently does not render live detection alerts or triage feeds.

---

## 6. Exactly ONE Next Recommended Step

**Phase 6: Frontend React Dashboard & Live Forensic Triage Interface**
- Implement interactive live triage view connecting to FastAPI WebSocket `/ws/jobs/{job_id}`.
- Build detection alert triage table with evidence drill-down, severity badges, and timeline correlation.
- Build JOCKY script editor with syntax validation and job dispatch controls.
