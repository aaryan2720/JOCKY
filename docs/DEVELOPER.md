# JOCKY Developer Documentation & Implementation Truth

## Implementation Status Table

| Component | Status |
|-----------|--------|
| JOCKY DSL | IMPLEMENTED |
| Agent runtime | IMPLEMENTED |
| Process collector | IMPLEMENTED |
| Network collector | IMPLEMENTED |
| Autorun collector | IMPLEMENTED |
| Scheduled task collector | IMPLEMENTED |
| User collector | IMPLEMENTED |
| Session collector | IMPLEMENTED |
| File collector | PLACEHOLDER |
| Driver collector | PLACEHOLDER |
| Service collector | PLACEHOLDER |
| Event log collector | PLACEHOLDER |
| Agent transport | IMPLEMENTED |
| Detection engine | IMPLEMENTED |
| Dashboard | IMPLEMENTED |

---

## 1. Last Completed Task
**Phase 7 — Frontend React Dashboard & Live Forensic Triage Interface**

---

## 2. Last Verified State

- **Frontend React / TypeScript Build & Tests**:
  - `npm test` (Vitest v1.6.0) -> **12/12 tests PASSED** in 2.74s across API client, error handling, telemetry normalization, and WebSocket protocol handling.
  - `npm run build` (`tsc && vite build`) -> **Production build SUCCESSFUL** (1517 modules transformed, 0 TypeScript errors, bundle size: 241 kB JS / 27 kB CSS).
- **Python Backend Test Suite**:
  - `python -m pytest -v` -> **62/62 tests PASSED** in 1.25s across detection, persistence, collectors, DSL, AST, planner, API routes, and WebSocket live feeds.
- **Go Agent Test Suite & Build**:
  - `go test -v -count=1 ./...` -> **31/31 tests PASSED** across `internal/collectors`, `internal/runtime`, and `tests`.
  - `go build ./...` -> **Binary build SUCCESSFUL** (exit code 0).

---

## 3. Current Working Functionality

The platform supports the complete end-to-end defensive forensic lifecycle:

```text
Analyst
   ↓ (JOCKY DSL Script)
React Frontend Dashboard
   ↓ (POST /api/v1/jobs with script_body)
FastAPI Management Server
   ↓ (JockyLexer → JockyParser → JockyPlanner)
Structured Versioned Execution Plan
   ↓ (Job Queue / Polling)
Go Endpoint Agent Runtime
   ↓ (Concurrent Read-Only Collectors)
Telemetry Collectors:
   • processes (read-only PID, cmdline, signatures)
   • connections (read-only sockets, ports, states)
   • autoruns (read-only Run/RunOnce, Startup, XDG)
   • scheduled_tasks (read-only schtasks, cron)
   • users (read-only local accounts, SIDs, shells)
   • sessions (read-only active sessions, terminals)
   ↓ (POST /api/v1/artifacts)
FastAPI Telemetry Ingestion
   ↓
Automated Adversary Detection & Correlation Engine
   ↓
Threat Detections Persistence & Live WebSocket Broadcast
   ↓ (ws://localhost:8000/ws/jobs/{job_id})
React Live Triage Console (Artifact Stream & Alert Inspection)
```

1. **Analyst Dashboard**: Comprehensive operational overview with fleet coverage metrics, active job status, artifact count, correlated threat detections, and endpoint collector health.
2. **Fleet Agents**: Real-time table of registered agents with status indicators (`online`, `offline`), platform filtering, certificate fingerprints, and 1-click investigation dispatch.
3. **JOCKY Investigation Editor**: Interactive DSL authoring environment with forensic templates (Persistence Triage, Process/Network Hunt, Identity Audit, Full Sweep), live server-side DSL syntax validation (`/api/v1/scripts/validate`), AST statements inspection, target agent multi-select, and plan dispatch.
4. **Jobs & Live Stream**: Dispatch queue and live monitoring interface subscribing to `/ws/jobs/{job_id}` with keep-alive pinging, automatic status transitions, and real-time artifact and threat notification cards.
5. **Artifact Results**: Multi-collector forensic viewer with type badges, summary representations for all 6 active collectors, granular search across telemetry fields, and detailed structured/raw inspection modals.
6. **Threat Detections**: Correlated alerts viewer with severity pills, deterministic rule explanations, and full supporting evidence chains linking each detection back to the originating telemetry artifacts.

---

## 4. Phase 7 — Frontend Architecture & Real-Time Triage

### 4.1 Frontend Architecture (`frontend/src/`)
```text
frontend/src/
  ├── api/
  │   ├── client.ts         # Centralized HTTP client, error parsing, and base URLs
  │   ├── agents.ts         # Agent fleet endpoints (list, get)
  │   ├── jobs.ts           # Job dispatch and retrieval endpoints
  │   ├── scripts.ts        # Script templates and live DSL validation
  │   ├── artifacts.ts      # Forensic artifact queries and inspection
  │   ├── detections.ts     # Threat detection queries and evidence chains
  │   ├── health.ts         # Backend service health check
  │   └── index.ts          # Consolidated exports
  ├── components/
  │   ├── common/
  │   │   ├── Badge.tsx     # Status and severity pills
  │   │   ├── Button.tsx    # Styled interactive buttons
  │   │   ├── Card.tsx      # Glassmorphic container with HTMLAttributes
  │   │   ├── EmptyState.tsx# Contextual empty state card
  │   │   ├── ErrorBanner.tsx # Sanitized service error banner
  │   │   └── LoadingSpinner.tsx # Animated forensic telemetry spinner
  │   └── layout/
  │       ├── AppLayout.tsx # Main grid layout
  │       ├── Navbar.tsx    # Brand header with live backend connection monitor
  │       └── Sidebar.tsx   # Six core forensic operations tabs
  ├── features/
  │   ├── dashboard/
  │   │   └── DashboardOverview.tsx # Metrics, quick actions, recent events
  │   ├── fleet/
  │   │   └── FleetTable.tsx        # Agent fleet management & detail drawer
  │   ├── editor/
  │   │   └── ScriptEditor.tsx      # JOCKY DSL editor, validator, and dispatcher
  │   ├── deployment/
  │   │   └── DeploymentList.tsx    # Job monitoring & WebSocket event stream
  │   ├── results/
  │   │   └── ArtifactViewer.tsx    # Artifact table, type filters, and inspector
  │   └── threats/
  │       └── ThreatAlertList.tsx   # Threat detections & evidence chain triage
  ├── hooks/
  │   └── useJobWebSocket.ts        # Resilient WebSocket connection hook
  ├── types/
  │   └── index.ts                  # TypeScript types for all models and WS events
  ├── App.tsx                       # Root application with cross-tab deep linking
  └── main.tsx                      # Vite React entry point
```

### 4.2 WebSocket Live Updates
- Endpoint: `/ws/jobs/{job_id}`
- Client Hook: `useJobWebSocket(jobId)` handles:
  - Connection lifecycle (`idle` → `connecting` → `connected` → `disconnected`)
  - Periodic keep-alive (`ping` / `pong` every 25s)
  - Message deserialization and event dispatching
  - Cleanup on unmount or job switch to prevent memory leaks and duplicate connections
- Stream Events:
  - `connected`: Initial subscription confirmation
  - `artifact_collected`: Real-time artifact telemetry with payload and agent ID
  - `threat_detected`: Automated detection event with triggering rule ID and severity
  - `job_status`: State transition notifications (`queued` → `running` → `completed`)

### 4.3 JOCKY DSL Validation & Submission
- Authoritative Backend Compiler: Frontend does not duplicate the DSL parser; it sends code to `/api/v1/scripts/validate` which executes `JockyLexer` and `JockyParser`.
- Compile feedback provides statement count, plan version, and target collectors before execution.
- Submissions create real jobs via `POST /api/v1/jobs` which are dispatched to the selected agents.

---

## 5. Current Contracts

### API Endpoints
- `GET /health`: Returns management server health and version.
- `GET /api/v1/agents`: List registered fleet agents with status filter.
- `GET /api/v1/agents/{agent_id}`: Retrieve agent details and certificate fingerprint.
- `POST /api/v1/agents/register`: Agent enrollment endpoint.
- `GET /api/v1/scripts`: List saved JOCKY investigation templates.
- `POST /api/v1/scripts`: Save new forensic script.
- `POST /api/v1/scripts/validate`: Validate DSL script syntax and return estimated collectors.
- `GET /api/v1/jobs`: List forensic job history.
- `GET /api/v1/jobs/{job_id}`: Retrieve job execution state, plan metadata, and timestamps.
- `POST /api/v1/jobs`: Dispatch compiled execution plan to target agents.
- `GET /api/v1/artifacts`: Query collected artifacts by `type`, `job_id`, `agent_id`, `limit`, `offset`.
- `GET /api/v1/artifacts/{artifact_id}`: Retrieve single artifact.
- `POST /api/v1/artifacts`: Ingest artifacts from agent, trigger detection, and broadcast over WebSocket.
- `GET /api/v1/detections`: Retrieve correlated detections by `severity`, `rule_id`, `status`, `job_id`, `agent_id`.
- `GET /api/v1/detections/{detection_id}`: Retrieve detection and supporting evidence chain.
- `WS /ws/jobs/{job_id}`: Real-time telemetry and alert event stream.

---

## 6. Current Limitations

1. **Placeholder Collectors**: The remaining four collectors (`files`, `drivers`, `services`, `event_logs`) remain safe placeholders.
2. **YARA & Sigma Engines**: In-depth binary scanning and Sigma rule engines are not yet integrated into the runtime.
3. **Agent Polling Loop**: Agents currently poll for jobs periodically rather than receiving push notifications via long-polling or gRPC.

---

## 7. Exactly ONE Next Recommended Step

**Phase 8: File System Collector & Hash Inspection**
- Implement read-only `files` collector on Windows and Linux (`FileCollector`).
- Safely inspect file metadata (path, size, timestamps, permissions, owner).
- Compute cryptographic file hashes (SHA-256, MD5) on demand in read-only mode.
- Prevent traversal into sensitive virtual filesystems (e.g. `/proc`, `/sys`).
- Integrate file hash artifacts with detection rules and the frontend artifact viewer.

---

## 8. Prior Completed Phases

### Phase 1 — JOCKY Language MVP
- Implemented lexer, parser, AST nodes, execution planner, and validation.
- Verbs: `scan`, `collect`, `hash`, `check`, `flag`, `report`.

### Phase 2 — Go Agent Execution Foundation
- Implemented execution runtime, typed execution plans, collector interface, and placeholder registry.

### Phase 3 — Process + Network Collectors
- Implemented read-only collectors for `processes` and `connections` with Windows/Linux platform separation.

### Phase 4 — Agent ↔ Server Transport
- Implemented agent registration, heartbeat loop, job polling, artifact submission, and bearer authentication boundary.

### Phase 5 — Detection & Correlation Engine
- Implemented explainable detection engine, persistence, deduplication, JOCKY `flag` dynamic condition evaluation, and `GET /api/v1/detections` API.

### Phase 6 — Persistence & Identity Collectors
- Implemented real read-only collectors for `autoruns`, `scheduled_tasks`, `users`, and `sessions` on Windows and Linux.
- Added rules `AUTORUN-SUSP-001` and `USER-SUSP-001`.
