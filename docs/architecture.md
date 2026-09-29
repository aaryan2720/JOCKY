# JOCKY System Architecture

## Overview

**JOCKY** is a high-performance, programmable Digital Forensics & Incident Response (DFIR) platform designed for live fleet interrogation, threat detection, and forensic artifact collection across distributed enterprise endpoints.

```
+-------------------------------------------------------------+
|                      Analyst / Operator                     |
+-------------------------------------------------------------+
                              |
                              v [HTTPS / WSS]
+-------------------------------------------------------------+
|               React Web Dashboard (Frontend)                |
|  - JOCKY Script Editor    - Fleet Overview & Health         |
|  - Live Job Deployment    - Forensic Artifact Viewer        |
|  - Real-time Timeline     - Threat & Alert Correlation      |
+-------------------------------------------------------------+
                              |
                              v [REST API + WebSocket]
+-------------------------------------------------------------+
|              FastAPI Management Server (Backend)            |
|  +-------------------------------------------------------+  |
|  | Core & API Routing (/api/v1/*, /ws/jobs/*)            |  |
|  +-------------------------------------------------------+  |
|  | JOCKY Language Engine (Lexer/Parser/AST/Interpreter)  |  |
|  +-------------------------------------------------------+  |
|  | Job Dispatcher & Execution Planner                    |  |
|  +-------------------------------------------------------+  |
|  | Agent Registry & Heartbeat Monitor                    |  |
|  +-------------------------------------------------------+  |
|  | Threat Detection & Correlation Engine (Sigma / YARA)  |  |
|  +-------------------------------------------------------+  |
|  | Database Layer (SQLAlchemy ORM + PostgreSQL)          |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
                              |
                              v [mTLS / HTTPS / gRPC]
+-------------------------------------------------------------+
|               Go Cross-Platform Forensic Agent              |
|  +-------------------------------------------------------+  |
|  | Agent Runtime Engine & Secure Transport               |  |
|  +-------------------------------------------------------+  |
|  | Read-Only Forensic Collectors:                        |  |
|  |  - Processes, Network sockets, Persistence / Autoruns |  |
|  |  - Scheduled tasks, Services, Drivers/Modules         |  |
|  |  - Event logs, File hashes, User sessions             |  |
|  |  - In-memory local rule matching (YARA / Heuristics)  |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
                              |
                              v [Read-Only OS Querying]
+-------------------------------------------------------------+
|               Windows / Linux Target Systems                |
+-------------------------------------------------------------+
```

---

## Architectural Principles & Rules

1. **Strict Decoupling**:
   - The Frontend communicates with the Backend strictly via REST and WebSocket contracts.
   - The Backend communicates with Agents via a transport-agnostic interface (HTTP/mTLS, later gRPC).
   - The JOCKY language engine is isolated in `backend/app/jocky/` with zero dependencies on FastAPI HTTP handlers.
2. **Defensive, Read-Only Forensics**:
   - JOCKY is explicitly forensic inspection software.
   - No offensive capabilities, exploitation primitives, AV/EDR evasion, process injection, or kernel tampering are permitted.
3. **Data Model Isolation**:
   - Database models (`backend/app/models/`) are kept separate from API schemas (`backend/app/schemas/`).
   - Route handlers delegate to services and orchestration layers.
4. **Agent Extensibility**:
   - Forensic collectors in Go implement a unified `Collector` interface (`Collect(ctx) ([]Artifact, error)`).
   - Transport implements a pluggable `Transport` interface (`SendReport`, `PollJobs`, `Register`).

---

## Core Entities & Data Model

| Entity | Fields | Description |
| :--- | :--- | :--- |
| **Agent** | `id`, `hostname`, `os`, `status`, `last_seen`, `cert_fingerprint`, `tags` | Registered endpoint running the Go agent |
| **Script** | `id`, `name`, `body`, `created_by`, `created_at`, `updated_at` | JOCKY DSL forensic script definitions |
| **Job** | `id`, `script_id`, `target_agent_ids`, `status`, `plan`, `created_at` | Execution unit dispatched across target agents |
| **Artifact** | `id`, `job_id`, `agent_id`, `type`, `data` (JSON), `collected_at` | Structured forensic evidence collected from endpoints |
| **Detection** | `id`, `job_id`, `agent_id`, `rule_name`, `severity`, `evidence`, `explanation` | Correlated security alert or suspicious anomaly |

---

## Security & Transport Model

- **Agent Authentication**: Initial registration via enrollment token, followed by mutual TLS (mTLS) certificate exchange.
- **Payload Integrity**: Execution plans produced by the JOCKY planner are digitally signed or hashed before dispatch.
- **Role-Based Access Control**: Backend enforces role boundaries (Analyst vs. Admin) for script execution and fleet management.
