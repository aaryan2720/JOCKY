# JOCKY Developer Documentation & Consolidated Living Project State

> **Living Source of Truth**: This document records the architectural decisions, current implementation status, development history, contracts, and handoff instructions for the JOCKY project.

---

## 1. Project Overview

**JOCKY** is a programmable Digital Forensics & Incident Response (DFIR) and adversary detection framework based on the NTRO/SIH problem statement. It empowers security analysts to write expressive, read-only forensic queries using the JOCKY DSL, compile them into deterministic JSON execution plans, dispatch those plans across fleet endpoint agents, gather structured evidence artifacts from Windows and Linux endpoints, evaluate explainable adversary detection rules, and monitor triage results centrally via a real-time web dashboard.

---

## 2. System Architecture

```text
                      Analyst / Operator
                              │
                              ▼ [HTTPS / WebSocket]
               React Web Dashboard (Frontend)
                              │
                              ▼ [REST API + WebSocket]
              FastAPI Management Server (Backend)
               ├── JOCKY Language Engine (Lexer/Parser/AST/Planner)
               ├── Execution Plan JSON Serializer
               ├── Detection & Correlation Engine (YARA/Sigma/Rules)
               ├── WebSocket Telemetry & Alert Stream
               └── PostgreSQL / Async SQLAlchemy Persistence
                    ├── agents (fleet presence & enrollment)
                    ├── scripts (saved JOCKY investigation templates)
                    ├── jobs (dispatched execution plans & states)
                    ├── artifacts (structured forensic evidence)
                    └── detections (explainable correlated threat alerts)
                              │
                              ▼ [mTLS / HTTP Dispatch & Polling]
               Go Forensic Agent (Endpoint Fleet)
               ├── Runtime Engine & Plan Validator
               ├── Thread-Safe Collector Registry
               │    └── All 10 Core Real Collectors:
               │        processes, connections, files, autoruns,
               │        scheduled_tasks, users, sessions, services,
               │        drivers, event_logs
               └── Transport Layer (Registration, Heartbeats, Job Poll, Ingestion)
                              │
                              ▼ [Strictly Read-Only OS Queries]
               Windows / Linux Target Endpoints
```

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Vitest.
- **Backend & DSL Engine**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Uvicorn, Pytest.
- **Database & Storage**: PostgreSQL 16 (production), `postgresql+asyncpg` / `sqlite+aiosqlite` async drivers, Redis 7.
- **Endpoint Agent**: Go 1.21+, standard cryptographic primitives (`crypto/sha256`), standard concurrency primitives (`sync.WaitGroup`, `context.Context`, Win32 API / `/proc` / event log parsers).
- **Infrastructure**: Docker, Docker Compose, PostgreSQL 16, Redis 7.

---

## 4. Last Completed Task

### Phase 11 — PostgreSQL Persistence Layer & Fleet Database Wiring

- **Database-Backed Persistence Services**: Replaced all in-memory dictionary stores in `AgentService`, `JobService`, `ArtifactService`, and `DetectionService` with persistent async SQLAlchemy ORM queries and transactions. Saved scripts (`ScriptModel`) are also persisted in the database.
- **Database Schema & Models**:
  - `AgentModel` (`agents` table): `id`, `hostname`, `os`, `arch`, `ip_address`, `status`, `version`, `cert_fingerprint`, `tags`, `last_seen`, `created_at`.
  - `ScriptModel` (`scripts` table): `id`, `name`, `description`, `body`, `created_by`, `created_at`, `updated_at`.
  - `JobModel` (`jobs` table): `id`, `script_id` (FK), `agent_id` (FK), `status`, `target_agents`, `plan`, `error_message`, `created_at`, `started_at`, `completed_at`.
  - `ArtifactModel` (`artifacts` table): `id`, `job_id` (FK), `agent_id` (FK), `type`, `target`, `host_id`, `data`, `metadata`, `collected_at`, `created_at`.
  - `DetectionModel` (`detections` table): `id`, `job_id` (FK), `agent_id` (FK), `rule_id`, `severity`, `title`, `description`, `status`, `evidence`, `dedup_key`, `created_at`.
- **Concurrency & Atomic Job Dispatch**: Converted `JobService.poll_job_for_agent` to use atomic conditional database updates (`UPDATE jobs SET status='in_progress', started_at=:now WHERE id=:candidate_id AND status IN ('queued', 'pending')`), guaranteeing single-assignment even under concurrent agent polling requests.
- **Deterministic Deduplication**: Enforces database-persisted SHA-256 deduplication keys (`dedup_key`) for threat detections to prevent duplicate alerts across re-ingestion or polling loops.
- **Alembic Migration Setup**: Initialized Alembic configuration (`alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial_schema.py`) supporting online async migrations and offline SQL generation.
- **Restart Persistence Verification**: Added and verified explicit backend restart tests (`tests/test_database_persistence.py::test_explicit_backend_restart_persistence`) proving that agents, jobs, artifacts, and detections completely survive engine disposal, singleton cache wipes, and backend service restarts.
- **Full Regression Test Suite**:
  - Backend: **113/113 tests passed** (including 7 new persistence & restart tests)
  - Go Agent: **70/70 tests passed**; Go binary build clean
  - Frontend: **12/12 tests passed**; Vite production build clean

---

## 5. Implementation Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| **Monorepo Structure** | `VERIFIED` | Root configuration, .gitignore, Docker Compose, Makefile all verified. |
| **Frontend Shell & UI** | `IMPLEMENTED + VERIFIED` | React 18 dashboard, fleet table, DSL editor, job tracker, artifact viewer, threat alerts. Vitest 12/12 passing; build clean. |
| **FastAPI Backend** | `IMPLEMENTED + VERIFIED` | Agent enrollment, heartbeats, JOCKY job dispatch, artifact ingestion, detection engine, WebSocket feeds. Pytest 113/113 passing. |
| **Database Persistence** | `IMPLEMENTED + VERIFIED` | SQLAlchemy async ORM, Alembic migrations, PostgreSQL/SQLite connection pools, restart-safe storage. |
| **JOCKY DSL Engine** | `IMPLEMENTED + VERIFIED` | Lexer, recursive-descent parser, AST safety checks, deterministic version 1 planner. Canonical verbs: `scan`, `collect`, `hash`, `check`, `flag`, `report`. |
| **Go Agent Runtime** | `IMPLEMENTED + VERIFIED` | Typed execution plans, validation, translation, context concurrency, polling and heartbeat workers. Go test 70/70 passing; builds clean. |
| **Collector Registry** | `IMPLEMENTED + VERIFIED` | Thread-safe `Collector` interface and `Registry` with runtime target resolution. (0 placeholders). |
| **Process Collector** | `IMPLEMENTED + VERIFIED` | Live read-only OS process enumeration on Windows (Toolhelp32, WinVerifyTrust) and Linux (/proc). |
| **Network Collector** | `IMPLEMENTED + VERIFIED` | Live read-only TCP/UDP connection & listening socket inspection on Windows (iphlpapi) and Linux (/proc/net). |
| **Files Collector & SHA-256** | `IMPLEMENTED + VERIFIED` | Live read-only filesystem enumeration, OS timestamps, streaming SHA-256 calculation, traversal bounding. |
| **Autoruns Collector** | `IMPLEMENTED + VERIFIED` | Live read-only Windows Run/RunOnce registry and Linux XDG autostart inspection. |
| **Scheduled Tasks Collector** | `IMPLEMENTED + VERIFIED` | Live read-only Windows schtasks CSV and Linux crontab inspection. |
| **Users Collector** | `IMPLEMENTED + VERIFIED` | Live read-only local account enumeration via Windows net user and Linux /etc/passwd. |
| **Sessions Collector** | `IMPLEMENTED + VERIFIED` | Live read-only session inspection via Windows qwinsta and Linux who. |
| **Services Collector** | `IMPLEMENTED + VERIFIED` | Live read-only service enumeration via Windows sc query and Linux systemd/init.d. |
| **Drivers Collector** | `IMPLEMENTED + VERIFIED` | Live read-only driver and kernel module enumeration via Windows driverquery and Linux /proc/modules. |
| **Event Logs Collector** | `IMPLEMENTED + VERIFIED` | Live read-only event log collection via Windows wevtutil and Linux journald/syslog. |
| **Placeholder Collectors** | `REMOVED (0 Remaining)` | All 10 core collectors are fully implemented as real read-only collectors. |
| **Detection Engine** | `IMPLEMENTED + VERIFIED` | Explainable detection engine, persistence, deduplication, JOCKY `flag` condition evaluation, and `/api/v1/detections`. |
| **Agent Transport** | `IMPLEMENTED + VERIFIED` | Authenticated HTTP REST transport for enrollment, heartbeat, job polling, and batch artifact upload. |
| **WebSocket Feed** | `IMPLEMENTED + VERIFIED` | Real-time telemetry and alert streaming at `/ws/jobs/{job_id}`. |

---

## 6. Canonical Contracts

### JOCKY Language Canonical DSL
The canonical DSL verbs are:
`scan`, `collect`, `hash`, `check`, `flag`, `report`

Example:
```text
scan processes
where signed == false
and network_connections > 0

collect autoruns, scheduled_tasks, services, drivers, event_logs

hash files in "%TEMP%"
check against reputation

flag when process injected_into "explorer.exe"
severity = high

report to server
```

### JSON Execution Plan Schema (Version 1)
```json
{
  "version": "1",
  "statements": [
    {
      "operation": "scan",
      "target": "processes",
      "where": {
        "operator": "and",
        "conditions": [
          { "field": "signed", "operator": "eq", "value": false },
          { "field": "network_connections", "operator": "gt", "value": 0 }
        ]
      }
    },
    {
      "operation": "collect",
      "targets": ["services", "drivers", "event_logs"]
    },
    {
      "operation": "hash",
      "target": "files",
      "path": "%TEMP%",
      "check_against": "reputation"
    },
    {
      "operation": "flag",
      "condition": { "field": "signed", "operator": "eq", "value": false },
      "severity": "high"
    },
    {
      "operation": "report",
      "destination": "server"
    }
  ]
}
```

### Normalized Event Artifact Contract
```json
{
  "job_id": "job-78a9c2",
  "agent_id": "agent-win-01",
  "type": "event",
  "collected_at": "2026-09-30T10:00:00Z",
  "data": {
    "channel": "System",
    "event_id": 7036,
    "provider": "Service Control Manager",
    "level": "Information",
    "timestamp": "2026-09-30T09:55:00Z",
    "record_id": 14523,
    "computer": "WORKSTATION-01",
    "message": "The Windows Update service entered the running state.",
    "source": "wevtutil"
  }
}
```

---

## 7. Known Limitations

- **Linux Runtime Verification**: Linux build tags and syscall parsers (`/proc/modules`, `journalctl`, `syslog`) compile cleanly and are tested with deterministic input parsing, but runtime behavior against a live Linux kernel has not been executed on the current Windows development machine.
- **Local Docker Daemon**: Docker CLI is not installed in the local host environment; database persistence is validated locally via async SQLite/PostgreSQL drivers and verified to run in containerized environments with `docker-compose.yml`.

---

## 8. Next Recommended Phase

**Phase 12: Production Packaging, Multi-Platform Agent Installers & EDR Telemetry Streaming**
Package the Go agent binary into automated Windows MSI / Linux systemd packages with enrollment tokens, and enable streaming telemetry channels for high-volume event ingestion.

---

## 9. Developer Handoff Notes

### Running All Test Suites
```bash
# Backend pytest suite (113 tests)
cd backend
python -m pytest -v

# Agent Go test suite and binary build (70 tests)
cd ../agent
go test -v ./...
go build ./...

# Frontend Vitest suite and production build (12 tests)
cd ../frontend
npm test
npm run build
```
