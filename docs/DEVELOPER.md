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
| **FastAPI Backend** | `SCAFFOLDED` | `GET /health` verified; route contracts documented. |
| **JOCKY Lexer** | `IMPLEMENTED` | Tokenizes keywords, targets, operators, literals, comments; line/col tracking. |
| **JOCKY Parser** | `IMPLEMENTED` | Recursive-descent parser producing typed AST; rejects offensive verbs. |
| **JOCKY AST** | `IMPLEMENTED` | Strongly typed dataclasses for statements, comparisons, and binary conditions. |
| **JOCKY Planner** | `IMPLEMENTED` | Compiles AST into versioned, deterministic JSON execution plans. |
| **Go Agent Runtime** | `IMPLEMENTED` | Strongly typed plan unmarshaling, validation, translation, and concurrency. |
| **Collector Interface & Registry** | `IMPLEMENTED` | Thread-safe `Collector` interface and `Registry` with runtime resolution. |
| **Process Collector** | `IMPLEMENTED + VERIFIED` | Live read-only OS process enumeration on Windows (Toolhelp32, WinVerifyTrust) and Linux (/proc). |
| **Network Collector** | `IMPLEMENTED + VERIFIED` | Live read-only TCP/UDP connection & listening socket inspection on Windows (iphlpapi) and Linux (/proc/net). |
| **Other Collectors** | `SCAFFOLDED` | 8 targets (`files`, `drivers`, `services`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `event_logs`) return explicit `ErrNotImplemented`. |
| **Agent Transport** | `NOT STARTED` | Transport interface defined; network mTLS/gRPC deferred to Phase 4. |
| **Detection Engine** | `NOT STARTED` | Stubs and AST flag instructions prepared. |
| **Database Persistence** | `SCAFFOLDED` | Async session configured; schema migrations deferred. |
| **mTLS Security** | `NOT STARTED` | Deferred to agent/server transport phase. |
| **WebSocket Feed** | `SCAFFOLDED` | Endpoint scaffolded; live push deferred to integration phase. |

---

## 6. Current Development Position

### Last Completed Task
Phase 3 — Core Forensic Collectors (Process & Network Telemetry).

### Last Verified State
- **Backend Pytest Suite**: **42 / 42 passed** (100% passing in 0.46s).
- **Go Agent Test Suite**: **17 / 17 passed** (including process/network collection, registry resolution, error handling, cancellation, and end-to-end plan execution).
- **Go Agent Executable**: Built cleanly to `agent/bin/jocky-agent.exe` and verified via `--one-shot`.

### Current Working Functionality
1. **JOCKY Language Compilation**: Lexes, parses, verifies AST safety rules, and generates version 1 JSON execution plans.
2. **Go Agent Plan Execution**: Validates typed execution plans, translates statements to internal requests, and dispatches collectors concurrently.
3. **Live Process Telemetry**:
   - **Windows**: Enumerates PIDs, PPIDs, process names, executable paths, command lines, security usernames via Windows APIs (`CreateToolhelp32Snapshot`, `QueryFullProcessImageNameW`, `OpenProcessToken`/`LookupAccountSidW`), and Authenticode signatures via `WinVerifyTrust` with thread-safe caching.
   - **Linux**: Enumerates PIDs, PPIDs, process names, executable paths, command lines, and UID/usernames via `/proc` filesystem (`/proc/[pid]/exe`, `/proc/[pid]/cmdline`, `/proc/[pid]/status`) with explicit `signature_status: "unsupported"`.
4. **Live Network Telemetry**:
   - **Windows**: Enumerates active listening sockets and TCP/UDP connections with local/remote IP addresses, ports, connection states, and owning PIDs via `iphlpapi.dll` (`GetExtendedTcpTable`, `GetExtendedUdpTable`).
   - **Linux**: Parses active IPv4/IPv6 TCP and UDP sockets from `/proc/net/tcp`, `/proc/net/tcp6`, `/proc/net/udp`, `/proc/net/udp6`, resolving socket inodes to owning process PIDs.
5. **Normalized Artifact Boundary**: Produces standardized `Artifact` structures (`type: "process"`, `type: "network_connection"`) across all platforms.
6. **Robust Error Handling**: Resilient to permission errors (`ACCESS_DENIED`), transient process lifecycles, and context cancellations without crashing or returning fake data.

### Current Limitations
1. **Remaining Collectors**: 8 targets (`files`, `drivers`, `services`, `autoruns`, `scheduled_tasks`, `users`, `sessions`, `event_logs`) remain explicit placeholders returning `ErrNotImplemented`.
2. **Transport Layer**: The agent operates standalone in memory and via CLI `--one-shot`; mTLS/gRPC agent-to-server communication is not yet wired.
3. **Detection Engine**: Artifacts are collected into memory; rule evaluation (YARA/Sigma/heuristics) is not yet active.

### Current Contracts
- **JOCKY Execution Plan**: Python compiler $\rightarrow$ JSON execution plan (`version: "1"`).
- **Agent Runtime**: JSON plan $\rightarrow$ Go runtime validator $\rightarrow$ typed instruction dispatch.
- **Collector Boundary**: `Collector` interface (`Collect(ctx, req) ([]Artifact, error)`) $\rightarrow$ normalized `Artifact` model (`ID`, `Type`, `Target`, `Timestamp`, `HostID`, `Data`, `Metadata`).

### Next Recommended Step
**Phase 4 — Agent-Server Transport & Heartbeat (mTLS / HTTP Dispatch)**:
Implement the network communication layer between the FastAPI backend and Go agent:
1. Endpoint registration and heartbeat handshake over authenticated HTTP/mTLS.
2. Job polling / dispatch mechanism allowing the backend to push compiled JOCKY execution plans to agents.
3. Secure artifact ingestion endpoint in the backend for storing and streaming collected artifacts.

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
  - **Windows** (`processes_windows.go`): `CreateToolhelp32Snapshot` process iteration, `QueryFullProcessImageNameW`, process token SID lookup for username, and Authenticode signature verification via `WinVerifyTrust` with thread-safe caching and revocation skip flags for high performance.
  - **Linux** (`processes_linux.go`): Read-only `/proc` inspection (`/proc/[pid]/exe`, `/proc/[pid]/cmdline`, `/proc/[pid]/status`) with explicit `signature_status: "unsupported"`.
- Implemented `NetworkCollector` in `agent/internal/collectors/network.go`:
  - **Windows** (`network_windows.go`): TCP and UDP socket enumeration (listening and established) using `iphlpapi.dll` (`GetExtendedTcpTable`, `GetExtendedUdpTable`).
  - **Linux** (`network_linux.go`): Read-only `/proc/net/tcp`, `/proc/net/tcp6`, `/proc/net/udp`, `/proc/net/udp6` parsing with socket inode-to-PID resolution.
- Updated `NewDefaultRegistry()`: Replaced placeholder collectors for `processes` and `connections` with real collectors while retaining explicit placeholders for the remaining 8 targets.
- Maintained zero breaking changes to existing contracts.
- Added comprehensive unit tests and end-to-end plan execution verification (17 / 17 Go tests passing).

---

## 8. Current Contracts

### JOCKY Pipeline Contract
$$\text{Source Code (.jky)} \longrightarrow \text{Tokens} \longrightarrow \text{Typed AST} \longrightarrow \text{JSON Execution Plan} \longrightarrow \text{Go Agent Runtime}$$

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
2. **Decoupled Collector Abstraction**: The runtime communicates with collectors solely through the `Collector` interface (`Name`, `Supports`, `Collect`), isolating OS-specific telemetry mechanisms (Windows APIs / Linux procfs) from orchestration logic.
3. **No Fake Forensic Data**: Placeholder collectors explicitly return `ErrNotImplemented` rather than dummy artifacts to preserve forensic integrity.
4. **Defensive Read-Only Primitives**: The execution plan and agent request models contain zero primitives for process injection, payload execution, or host modification.
5. **Context-Aware Concurrency**: All collection requests are dispatched concurrently using goroutines while respecting `context.Context` cancellation and timeout deadlines.

---

## 10. Known Issues & Limitations

- **Forensic Collectors**: Live Windows/Linux OS telemetry collectors are not yet implemented (scheduled for Phase 3).
- **Transport**: Agent-to-server mTLS / gRPC communication layer is currently mocked with local identity enrollment.

---

## 11. Next Recommended Step

**Phase 3 — Core Forensic Collectors (Process & Network Telemetry)**:
Implement the first set of read-only OS collectors in Go:
1. `ProcessCollector`: Inspect running processes, command lines, parent PIDs, and digital signature status on Windows/Linux.
2. `NetworkCollector`: Enumerate active listening and established TCP/UDP sockets associated with processes.
3. Integrate real collectors into the `Registry` to replace their respective placeholders.

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
- `agent/internal/runtime/`: Plan structures, validator, translator, and execution orchestrator.
- `agent/internal/collectors/`: Collector interface, artifact model, and registry.
