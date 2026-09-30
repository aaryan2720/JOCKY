# JOCKY Developer Documentation & Living Project State

> **Living Source of Truth**: This document records the architectural decisions, current implementation status, development history, contracts, and handoff instructions for the JOCKY project.

---

## 1. Project Overview

**JOCKY** is a programmable Digital Forensics & Incident Response (DFIR) and adversary detection framework. It empowers security analysts to write expressive, read-only forensic queries using the JOCKY DSL, compile them into deterministic JSON execution plans, dispatch those plans across fleet endpoint agents, gather structured evidence artifacts, evaluate detection rules, and monitor triage results centrally.

---

## 2. Current Architecture

```
                      Analyst / Operator
                              │
                              ▼ [HTTPS / WebSocket]
               React Web Dashboard (Frontend)
                              │
                              ▼ [REST API + WebSocket]
              FastAPI Management Server (Backend)
               ├── JOCKY Language Engine (Lexer/Parser/AST/Planner)
               ├── Execution Plan JSON Serializer
               └── Future: DB Persistence, RBAC, Dispatcher
                              │
                              ▼ [mTLS / HTTP / gRPC]
               Go Forensic Agent (Endpoint)
               ├── Runtime Engine & Plan Validator
               ├── Collector Registry (10 Target Placeholders)
               └── Future: OS-specific Collectors (Win/Linux), Local Detection
                              │
                              ▼ [Read-Only OS Queries]
               Windows / Linux Target Systems
```

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, ESLint, Prettier.
- **Backend & DSL Engine**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Uvicorn, Pytest.
- **Endpoint Agent**: Go 1.21+, standard concurrency primitives (`sync.WaitGroup`, `context.Context`).
- **Infrastructure**: Docker, Docker Compose, PostgreSQL 16, Redis 7.

---

## 4. Repository Structure

```
jocky/
├── README.md               # Monorepo onboarding & quickstart
├── .gitignore              # Multi-tier exclusion rules
├── .env.example            # Environment configuration template
├── docker-compose.yml      # Local Postgres & Redis orchestration
├── Makefile                # Unified build/test commands
├── frontend/               # React 18 dashboard scaffold
├── backend/                # FastAPI management server & JOCKY language engine
│   ├── app/
│   │   ├── api/            # REST and WebSocket route stubs
│   │   ├── core/           # Configuration & settings
│   │   ├── db/             # SQLAlchemy async engine
│   │   ├── models/         # Database ORM models
│   │   ├── schemas/        # Pydantic DTOs
│   │   └── jocky/          # Lexer, Parser, AST, Interpreter, Planner
│   └── tests/              # Backend test suites (42 tests)
├── agent/                  # Go endpoint forensic agent
│   ├── cmd/agent/          # main.go executable entry point
│   ├── internal/
│   │   ├── collectors/     # Collector interface & Registry
│   │   ├── runtime/        # Plan types, Validator, Translation, Engine
│   │   ├── registration/   # Endpoint identity handshake
│   │   └── transport/      # Transport contract interfaces
│   └── tests/              # Go agent test suite (15 tests)
├── docs/                   # Specifications, architecture, guides, and DEVELOPER.md
├── rules/                  # YARA & Sigma detection rule repositories
├── database/               # Migrations & seed datasets
└── scripts/                # Dev orchestration runners
```

---

## 5. Implementation Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| **Monorepo Structure** | `VERIFIED` | Root configuration, .gitignore, Docker Compose, Makefile all verified. |
| **Frontend Shell** | `SCAFFOLDED` | Navigation, layout, fleet view, editor view, build/lint pass. |
| **FastAPI Backend** | `IMPLEMENTED + VERIFIED` | Health check, agent enrollment, heartbeat tracking, JOCKY job dispatch, and artifact ingestion verified. |
| **JOCKY Lexer** | `IMPLEMENTED` | Tokenizes keywords, targets, operators, literals, comments; line/col tracking. |
| **JOCKY Parser** | `IMPLEMENTED` | Recursive-descent parser producing typed AST; rejects offensive verbs. |
| **JOCKY AST** | `IMPLEMENTED` | Strongly typed dataclasses for statements, comparisons, and binary conditions. |
| **JOCKY Planner** | `IMPLEMENTED` | Compiles AST into versioned, deterministic JSON execution plans. |
| **Go Agent Runtime** | `IMPLEMENTED` | Strongly typed plan unmarshaling, validation, translation, concurrency, and background poll/heartbeat worker. |
| **Collector Interface & Registry** | `IMPLEMENTED` | Thread-safe `Collector` interface and `Registry` with runtime resolution. |
| **Process Collector** | `IMPLEMENTED + VERIFIED` | Live read-only OS process enumeration on Windows (Toolhelp32, WinVerifyTrust) and Linux (/proc). |
| **Network Collector** | `IMPLEMENTED + VERIFIED` | Live read-only TCP/UDP connection & listening socket inspection on Windows (iphlpapi) and Linux (/proc/net). |
| **Other Collectors** | `SCAFFOLDED` | 8 targets (`files`, `drivers`, `services`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `event_logs`) return explicit `ErrNotImplemented`. |
| **Agent Transport** | `IMPLEMENTED + VERIFIED` | Authenticated HTTP REST transport for enrollment, heartbeat, job polling, and batch artifact upload. |
| **Detection Engine** | `NOT STARTED` | Stubs and AST flag instructions prepared. |
| **Database Persistence** | `SCAFFOLDED` | In-memory fleet/job/artifact repository active; PostgreSQL migrations deferred. |
| **mTLS Security** | `NOT STARTED` | Token-based HTTP authorization active; mTLS certificate authority deferred to future hardening. |
| **WebSocket Feed** | `SCAFFOLDED` | Endpoint scaffolded; live push deferred to integration phase. |

---

## 6. Current Development Position

### Last Completed Task
Phase 4 — Agent-Server Transport & Heartbeat (HTTP Dispatch & Ingestion).

### Last Verified State
- **Backend Pytest Suite**: **45 / 45 passed** (100% passing in 0.73s).
- **Go Agent Test Suite**: **20 / 20 passed** (including process/network collection, registry resolution, HTTP transport mock testing, error handling, and end-to-end job poll/execute/ingest cycle).
- **Go Agent Executable**: Built cleanly to `agent/bin/jocky-agent.exe` and verified via `--one-shot`.

### Current Working Functionality
1. **JOCKY Language Compilation**: Lexes, parses, verifies AST safety rules, and generates version 1 JSON execution plans.
2. **Go Agent Plan Execution**: Validates typed execution plans, translates statements to internal requests, and dispatches collectors concurrently.
3. **Live Process & Network Telemetry**:
   - **Windows**: Enumerates PIDs, PPIDs, process names, executable paths, command lines, security usernames, Authenticode signatures, and TCP/UDP sockets via Win32 APIs.
   - **Linux**: Enumerates PIDs, PPIDs, names, executable paths, command lines, and TCP/UDP sockets via `/proc` filesystem.
4. **Agent Enrollment & Presence**:
   - Agent self-registers via `POST /api/v1/agents/register` and receives `agent_id` and `heartbeat_interval_seconds`.
   - Agent background worker periodically emits heartbeats via `POST /api/v1/agents/{agent_id}/heartbeat`, tracking live fleet presence.
5. **Job Dispatch & Execution Pipeline**:
   - Analysts submit JOCKY DSL scripts via `POST /api/v1/jobs`.
   - Backend automatically compiles the script to a structured execution plan and queues it for target agents.
   - Agent polls queued jobs via `GET /api/v1/agents/{agent_id}/jobs/poll`, validates and executes the plan locally, and harvests live telemetry.
6. **Artifact Ingestion & Storage**:
   - Agent submits collected forensic artifacts via `POST /api/v1/artifacts`.
   - Backend ingests artifacts, updates job status to `completed`, and exposes artifacts via `GET /api/v1/artifacts`.

### Current Limitations
1. **Remaining Collectors**: 8 targets (`files`, `drivers`, `services`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `event_logs`) remain explicit placeholders returning `ErrNotImplemented`.
2. **Detection Engine**: Artifacts are ingested into storage; automated adversary detection rule evaluation (YARA/Sigma/heuristics) is not yet active.

### Current Contracts
- **JOCKY Execution Plan**: Python compiler $\rightarrow$ JSON execution plan (`version: "1"`).
- **Agent-Server Transport**:
  - Enrollment: `POST /api/v1/agents/register` $\rightarrow$ `AgentRegisterResponse`
  - Heartbeat: `POST /api/v1/agents/{agent_id}/heartbeat` $\rightarrow$ `AgentHeartbeatResponse`
  - Job Poll: `GET /api/v1/agents/{agent_id}/jobs/poll` $\rightarrow$ `JobPollResponse`
  - Ingestion: `POST /api/v1/artifacts` $\rightarrow$ `ArtifactSubmissionResponse`
- **Collector Boundary**: `Collector` interface (`Collect(ctx, req) ([]Artifact, error)`) $\rightarrow$ normalized `Artifact` model.

### Next Recommended Step
**Phase 5 — Adversary Detection & Correlation Engine**:
Implement the detection engine analyzing collected artifacts against threat detection rules:
1. Heuristic and anomaly correlation (e.g., unsigned binaries with active network connections, suspicious parent-child relationships).
2. Rule engine structure for evaluating flagged conditions.
3. Alert generation and exposure via `GET /api/v1/detections`.

---

## 7. Development History

### Phase 0 — Monorepo Foundation
- Established root repository, `.env.example`, `docker-compose.yml`, `Makefile`, and directory skeletons.
- Configured FastAPI `GET /health` responding with `{"status": "ok", "service": "jocky-backend"}`.
- Scaffolded React Vite dashboard and Go agent skeleton.

### Phase 1 — JOCKY Language MVP
- Implemented `backend/app/jocky/` (lexer, parser, AST, interpreter, planner, public API).
- Enforced strict read-only safety policy; rejected offensive primitives (`execute`, `inject`, `load`, `disable`, `write`, `delete`, `kill`, `shell`).
- Created public Python APIs: `compile_jocky(source)`, `compile_jocky_to_json(source)`, `parse_jocky(source)`, `tokenize_jocky(source)`.
- Verified with 42 unit and end-to-end tests.

### Phase 2 — Go Agent Execution Foundation
- Defined strongly-typed Go structures for execution plans (`ExecutionPlan`, `ExecutionStatement`, `ConditionClause`).
- Implemented `ValidatePlan` with structured `PlanValidationError` reporting statement indices and fields.
- Created `Collector` interface, `CollectionRequest`, `Artifact` model, and thread-safe `Registry`.
- Implemented default placeholder collectors for all 10 core targets (`processes`, `connections`, `files`, `drivers`, `services`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `event_logs`) returning explicit `ErrNotImplemented` errors (zero fake forensic data).
- Implemented `TranslatePlan` converting plans into typed `CollectionRequest`, `HashRequest`, `CheckRequest`, `FlagInstruction`, and `ReportInstruction`.
- Built `AgentRuntime.ExecutePlan` with concurrent collection worker orchestration and `context.Context` cancellation propagation.
- Verified with 15 Go tests.

### Phase 3 — Core Forensic Collectors (Process & Network Telemetry)
- Implemented `ProcessCollector` in `agent/internal/collectors/processes.go`:
  - **Windows** (`processes_windows.go`): `CreateToolhelp32Snapshot` process iteration, `QueryFullProcessImageNameW`, process token SID lookup for username, and Authenticode signature verification via `WinVerifyTrust` with thread-safe caching.
  - **Linux** (`processes_linux.go`): Read-only `/proc` inspection (`/proc/[pid]/exe`, `/proc/[pid]/cmdline`, `/proc/[pid]/status`) with explicit `signature_status: "unsupported"`.
- Implemented `NetworkCollector` in `agent/internal/collectors/network.go`:
  - **Windows** (`network_windows.go`): TCP and UDP socket enumeration (listening and established) using `iphlpapi.dll` (`GetExtendedTcpTable`, `GetExtendedUdpTable`).
  - **Linux** (`network_linux.go`): Read-only `/proc/net/tcp`, `/proc/net/tcp6`, `/proc/net/udp`, `/proc/net/udp6` parsing with socket inode-to-PID resolution.
- Updated `NewDefaultRegistry()`: Replaced placeholder collectors for `processes` and `connections` with real collectors while retaining explicit placeholders for the remaining 8 targets.
- Verified with 17 Go tests and 42 Python tests.

### Phase 4 — Agent-Server Transport & Heartbeat (mTLS / HTTP Dispatch)
- Implemented concrete HTTP transport layer in `agent/internal/transport/http_transport.go`:
  - `Register`: Bootstraps enrollment with server.
  - `SendHeartbeat`: Periodically reports agent status and presence.
  - `PollJob`: Long-polls pending forensic execution plans dispatched from the server.
  - `SubmitArtifacts`: Submits collected forensic evidence batches to the management server.
- Built backend management services and endpoints:
  - `AgentService`: In-memory fleet tracking, enrollment, and heartbeat recording (`POST /api/v1/agents/register`, `POST /api/v1/agents/{id}/heartbeat`, `GET /api/v1/agents`).
  - `JobService`: JOCKY DSL script compilation, dispatch queueing, agent job polling (`POST /api/v1/jobs`, `GET /api/v1/agents/{id}/jobs/poll`).
  - `ArtifactService`: Batch artifact ingestion and filtering (`POST /api/v1/artifacts`, `GET /api/v1/artifacts`).
- Built Go agent background polling and heartbeat routines in `AgentRuntime.Start` and `AgentRuntime.PollAndExecuteNextJob`.
- Verified with 20 Go tests and 45 Python backend tests.

---

## 8. Current Contracts

### JOCKY Pipeline Contract
$$\text{Source Code (.jky)} \longrightarrow \text{Tokens} \longrightarrow \text{Typed AST} \longrightarrow \text{JSON Execution Plan} \longrightarrow \text{Agent Transport Dispatch} \longrightarrow \text{Go Agent Runtime} \longrightarrow \text{Artifact Ingestion}$$

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

## 9. Important Design Decisions

1. **Strongly Typed Go Structures**: The Go agent runtime models the JSON execution plan explicitly rather than relying on `map[string]any` to guarantee compile-time safety and deterministic validation.
2. **Decoupled Collector Abstraction**: The runtime communicates with collectors solely through the `Collector` interface (`Name`, `Supports`, `Collect`), isolating OS-specific telemetry mechanisms from orchestration logic.
3. **No Fake Forensic Data**: Placeholder collectors explicitly return `ErrNotImplemented` rather than dummy artifacts to preserve forensic integrity.
4. **Defensive Read-Only Primitives**: The execution plan and agent request models contain zero primitives for process injection, payload execution, or host modification.
5. **Context-Aware Concurrency**: All collection requests are dispatched concurrently using goroutines while respecting `context.Context` cancellation and timeout deadlines.
6. **Resilient Long-Polling Transport**: Agent gracefully handles disconnects, retries on polling intervals, and falls back to offline identity when running isolated.

---

## 10. Known Issues & Limitations

- **Remaining Collectors**: 8 targets (`files`, `drivers`, `services`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `event_logs`) return explicit `ErrNotImplemented`.
- **Detection Correlation**: Ingested artifacts are persisted in memory; rule correlation (YARA/Sigma/heuristics) is not yet active.

---

## 11. Next Recommended Step

**Phase 5 — Adversary Detection & Correlation Engine**:
Implement backend detection heuristics and rule evaluation against ingested forensic artifacts:
1. Threat correlation engine matching suspicious process parentage and unsigned network sockets.
2. Flag statement evaluation mapping JOCKY `flag` rules to structured security alerts.
3. Alert retrieval endpoints (`GET /api/v1/detections`).

---

## 12. Developer Handoff Notes

### Running Test Suites
```bash
# Backend tests (Python pytest)
cd backend
python -m pytest -v

# Agent tests (Go test)
cd agent
go test -v ./...
```

### Building the Go Agent
```bash
cd agent
go build -o bin/jocky-agent.exe cmd/agent/main.go
.\bin\jocky-agent.exe --one-shot
```

### Key Directories
- `backend/app/jocky/`: JOCKY compiler (Lexer, Parser, AST, Planner, Public API).
- `backend/app/services/`: Agent, Job, and Artifact lifecycle management.
- `agent/internal/transport/`: Agent HTTP transport and DTO definitions.
- `agent/internal/runtime/`: Plan validator, translator, and execution orchestrator.
- `agent/internal/collectors/`: Collector interface, artifact model, and OS implementations.

