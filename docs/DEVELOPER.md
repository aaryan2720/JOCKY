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
               └── In-Memory / PostgreSQL Persistence
                              │
                              ▼ [mTLS / HTTP Dispatch & Polling]
               Go Forensic Agent (Endpoint Fleet)
               ├── Runtime Engine & Plan Validator
               ├── Thread-Safe Collector Registry
               │    ├── Real: processes, connections, autoruns,
               │    │         scheduled_tasks, users, sessions
               │    └── Placeholders: files, drivers, services, event_logs
               └── Transport Layer (Registration, Heartbeats, Job Poll, Ingestion)
                              │
                              ▼ [Strictly Read-Only OS Queries]
               Windows / Linux Target Endpoints
```

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Vitest.
- **Backend & DSL Engine**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Uvicorn, Pytest.
- **Endpoint Agent**: Go 1.21+, standard concurrency primitives (`sync.WaitGroup`, `context.Context`, Win32 API / `/proc` parsers).
- **Infrastructure**: Docker, Docker Compose, PostgreSQL 16, Redis 7.

---

## 4. Repository Structure

```text
jocky/
├── README.md               # Monorepo onboarding & quickstart
├── .gitignore              # Multi-tier exclusion rules
├── .env.example            # Environment configuration template
├── docker-compose.yml      # Local Postgres & Redis orchestration
├── Makefile                # Unified build/test commands
├── frontend/               # React 18 dashboard & triage console
│   ├── src/
│   │   ├── api/            # REST client endpoints (agents, jobs, scripts, artifacts, detections)
│   │   ├── components/     # Reusable layout and UI elements
│   │   ├── features/       # Dashboard, Fleet, Editor, Jobs, Results, Threats
│   │   └── hooks/          # useJobWebSocket real-time feed hook
│   └── src/__tests__/      # Vitest test suites
├── backend/                # FastAPI management server & JOCKY language engine
│   ├── app/
│   │   ├── api/            # REST and WebSocket routes (agents, artifacts, detections, jobs, scripts)
│   │   ├── core/           # Configuration & settings
│   │   ├── db/             # SQLAlchemy async engine & base
│   │   ├── detection/      # Explainable detection engine & threat rules
│   │   ├── models/         # ORM models (agents, jobs, artifacts, detections)
│   │   ├── schemas/        # Pydantic v2 DTO schemas
│   │   ├── services/       # Lifecycle services (AgentService, JobService, ArtifactService, DetectionService)
│   │   └── jocky/          # Canonical DSL compiler (Lexer, Parser, AST, Planner)
│   └── tests/              # Pytest suites (62 tests)
├── agent/                  # Go endpoint forensic agent
│   ├── cmd/agent/          # main.go executable entry point
│   ├── internal/
│   │   ├── collectors/     # Collector interface, Registry, Windows/Linux OS implementations
│   │   ├── runtime/        # Execution plan unmarshaling, validation, translation, concurrency engine
│   │   ├── registration/   # Endpoint identity handshake
│   │   ├── detection/      # Local evaluation stubs
│   │   └── transport/      # Authenticated HTTP REST transport
│   └── tests/              # Go agent test suites (31 tests)
├── docs/                   # Specifications, architecture, guides, and DEVELOPER.md
├── rules/                  # YARA & Sigma detection rule definitions
├── database/               # Migrations & seed datasets
└── scripts/                # Dev orchestration runners
```

---

## 5. Implementation Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| **Monorepo Structure** | `VERIFIED` | Root configuration, .gitignore, Docker Compose, Makefile all verified. |
| **Frontend Shell & UI** | `IMPLEMENTED + VERIFIED` | React 18 dashboard, fleet table, DSL editor, job tracker, artifact viewer, threat alerts. Vitest 12/12 passing; build clean. |
| **FastAPI Backend** | `IMPLEMENTED + VERIFIED` | Agent enrollment, heartbeats, JOCKY job dispatch, artifact ingestion, detection engine, WebSocket feeds. Pytest 62/62 passing. |
| **JOCKY DSL Engine** | `IMPLEMENTED + VERIFIED` | Lexer, recursive-descent parser, AST safety checks, deterministic version 1 planner. Canonical verbs: `scan`, `collect`, `hash`, `check`, `flag`, `report`. |
| **Go Agent Runtime** | `IMPLEMENTED + VERIFIED` | Typed execution plans, validation, translation, context concurrency, polling and heartbeat workers. Go test 31/31 passing; builds clean. |
| **Collector Registry** | `IMPLEMENTED + VERIFIED` | Thread-safe `Collector` interface and `Registry` with runtime target resolution. |
| **Process Collector** | `IMPLEMENTED + VERIFIED` | Live read-only OS process enumeration on Windows (Toolhelp32, WinVerifyTrust) and Linux (/proc). |
| **Network Collector** | `IMPLEMENTED + VERIFIED` | Live read-only TCP/UDP connection & listening socket inspection on Windows (iphlpapi) and Linux (/proc/net). |
| **Autoruns Collector** | `IMPLEMENTED + VERIFIED` | Live read-only Windows Run/RunOnce registry and Linux XDG autostart inspection. |
| **Scheduled Tasks Collector** | `IMPLEMENTED + VERIFIED` | Live read-only Windows schtasks CSV and Linux crontab inspection. |
| **Users Collector** | `IMPLEMENTED + VERIFIED` | Live read-only local account enumeration via Windows net user and Linux /etc/passwd. |
| **Sessions Collector** | `IMPLEMENTED + VERIFIED` | Live read-only session inspection via Windows qwinsta and Linux who. |
| **Placeholder Collectors** | `SCAFFOLDED` | 4 targets (`files`, `drivers`, `services`, `event_logs`) return safe placeholder artifacts without crashing. |
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

collect autoruns, scheduled_tasks, services

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
      "targets": ["autoruns", "scheduled_tasks"]
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

## 7. Developer Handoff Notes

### Running All Test Suites
```bash
# Backend pytest suite
cd backend
python -m pytest -v

# Agent Go test suite and binary build
cd ../agent
go test -v ./...
go build ./...

# Frontend Vitest suite and production build
cd ../frontend
npm test
npm run build
```
