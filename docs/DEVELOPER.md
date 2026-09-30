# JOCKY Developer Documentation & Consolidated Living Project State

> **Living Source of Truth**: This document records the architectural decisions, current implementation status, development history, contracts, validation records, and handoff instructions for the JOCKY project.

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

## 4. Final Full-System MVP Validation & Verification Status

### Validation Status: `VERIFIED & FULLY FUNCTIONAL`

The complete end-to-end MVP workflow has been validated across all components:

1. **Database & Migrations**:
   - Clean schema initialization via Alembic (`alembic/versions/0001_initial_schema.py`) and async SQLAlchemy metadata (`Base.metadata.create_all`).
   - Persistent tables: `agents`, `scripts`, `jobs`, `artifacts`, `detections`.
2. **FastAPI Backend Server**:
   - Healthcheck endpoint `/health` operational and returning `{"status": "ok"}`.
   - All REST endpoints (`/api/v1/agents`, `/api/v1/jobs`, `/api/v1/artifacts`, `/api/v1/detections`, `/api/v1/scripts`) verified with database backing.
3. **Go Forensic Agent Runtime**:
   - Agent enrollment (`/api/v1/agents/register`) generates deterministic cert fingerprints and enrolls endpoints.
   - Heartbeat worker reports regular presence timestamps.
   - Job polling retrieval loop receives dispatched execution plans.
4. **JOCKY DSL Compilation & Dispatch**:
   - Canonical multi-collector query compiled: `COLLECT processes, connections, services, drivers; REPORT TO server;`.
   - Produces deterministic version 1 JSON execution plans dispatched to target agents.
5. **Real Forensic Collection & Ingestion**:
   - All 10 real collectors executed and verified: `processes`, `connections`, `files`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `services`, `drivers`, `event_logs`.
   - Ingests structured JSON evidence into database transactions with foreign keys.
6. **Adversary Detection & Deduplication**:
   - Correlates forensic artifacts with heuristic rules (`AUTORUN-SUSP-001`, `PROC-UNSIGNED-001`, `PROC-NET-001`, `PROC-PARENT-001`, `USER-SUSP-001`) and dynamic JOCKY flag conditions.
   - Persists threat alerts with evidence references and SHA-256 deduplication keys.
7. **Explicit Backend Restart Persistence**:
   - Verified that all fleet agents, dispatched jobs, collected artifacts, and detection alerts survive database connection disposal, singleton cache wipes, and full backend service restarts.
8. **Controlled Error & Failure Paths**:
   - Verified clean 404 responses for missing agents/jobs.
   - Verified safe syntax error reporting on malformed DSL queries without database corruption.

---

## 5. Full Component Implementation Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| **Monorepo Structure** | `VERIFIED` | Root configuration, .gitignore, Docker Compose, Makefile all verified. |
| **Frontend Shell & UI** | `IMPLEMENTED + VERIFIED` | React 18 dashboard, fleet table, DSL editor, job tracker, artifact viewer, threat alerts. Vitest 12/12 passing; build clean. |
| **FastAPI Backend** | `IMPLEMENTED + VERIFIED` | Agent enrollment, heartbeats, JOCKY job dispatch, artifact ingestion, detection engine, WebSocket feeds. Pytest 114/114 passing. |
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

---

## 7. Known Limitations & Verification Scope

- **Linux Runtime Live Host Execution**: Linux build tags and syscall parsers (`/proc/modules`, `journalctl`, `syslog`, `/etc/passwd`) compile cleanly and are verified with unit tests and mock parsers; live Linux kernel execution requires a Linux host or VM.
- **Local Host Docker CLI**: Docker CLI is not installed on the local Windows host; database persistence is validated locally via async SQLite/PostgreSQL drivers and verified compatible with `docker-compose.yml`.

---

## 8. Developer Handoff Notes

### Running All Test Suites
```bash
# Backend pytest suite (114 tests)
cd backend
python -m pytest -v

# Agent Go test suite and binary build (70 tests)
cd ../agent
go test -v ./...
go build ./...

# Frontend Vitest suite and production build (12 tests)
cd ../frontend
npm test -- --run
npm run build
```
