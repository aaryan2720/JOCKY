# JOCKY - Programmable DFIR Platform

> **JOCKY** is a programmable Digital Forensics & Incident Response (DFIR) platform for endpoint interrogation, threat detection, and forensic evidence collection.

---

## Architecture Overview

```
Analyst
   │
   ▼
React Web Dashboard (Frontend)
   │  HTTPS/REST + WebSocket
   ▼
FastAPI Management Server (Backend)
   │  mTLS/HTTPS/gRPC
   ▼
Go Cross-Platform Forensic Agent
   │
   ▼
Windows / Linux Forensic Artifacts
```

---

## Monorepo Layout

```
jocky/
├── README.md               # Root project overview & onboarding
├── .gitignore              # Monorepo git ignore rules
├── .env.example            # Environment configuration template
├── docker-compose.yml      # Local container orchestration (Postgres, Redis, Backend)
├── Makefile                # Standard developer commands
├── frontend/               # React 18 + TypeScript + Vite + Tailwind CSS Dashboard
├── backend/                # FastAPI + Pydantic + SQLAlchemy Backend & JOCKY Engine
├── agent/                  # Go Cross-Platform Forensic Agent
├── rules/                  # Detection rule storage (YARA / Sigma)
├── database/               # Database migrations and seed datasets
├── infra/                  # Dockerfiles and infrastructure configs
├── docs/                   # Architecture, API specifications, and dev guides
└── scripts/                # Utility scripts (dev runners, health checks)
```

---

## Independent 2-Developer Work Split

To maximize speed and avoid merge conflicts during the hackathon, the codebase is modularized along clear boundaries:

| Developer | Scope / Primary Folders | Responsibilities |
| :--- | :--- | :--- |
| **Developer A** | `frontend/`, `backend/app/api/`, `backend/app/schemas/`, `backend/app/models/` | UI/UX dashboard, editor interface, fleet views, REST API routes, WebSocket integration, DB persistence. |
| **Developer B** | `agent/`, `backend/app/jocky/`, `backend/app/orchestration/`, `backend/app/detection/`, `rules/` | Go forensic collectors, agent runtime, JOCKY DSL parser/AST/planner, threat correlation engine, rule matching. |

---

## Prerequisites

- **Node.js**: v18+ and `npm`
- **Python**: 3.10+ (Recommended: 3.11)
- **Go**: 1.21+
- **Docker & Docker Compose** (for PostgreSQL and Redis)

---

## Quickstart Guide

### 1. Configure Environment
```bash
cp .env.example .env
```

### 2. Start Infrastructure (PostgreSQL & Redis)
```bash
make docker-up
# Or: docker compose up -d postgres redis
```

### 3. Start Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```
Check health: `curl http://localhost:8000/health` (or open http://localhost:8000/docs for Swagger UI).

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 to access the dashboard.

### 5. Start Forensic Agent
```bash
cd agent
go run cmd/agent/main.go
```
The agent will initialize and log `"JOCKY agent starting"`.

---

## Development Commands

| Command | Action |
| :--- | :--- |
| `make dev` | Start frontend and backend concurrently |
| `make backend` | Start backend server locally |
| `make frontend` | Start frontend dev server |
| `make agent` | Run the Go agent |
| `make test` | Run test suites across backend, frontend, and agent |
| `make lint` | Run code quality checks |
| `make format` | Run code formatters |
| `make docker-up` | Start PostgreSQL & Redis in Docker |
| `make docker-down` | Stop Docker infrastructure |

---

## Documentation

Detailed documentation is available in [`/docs`](file:///d:/Documents/JOCKY/docs):
- [Architecture & Design Rules](file:///d:/Documents/JOCKY/docs/architecture.md)
- [API Contract & Specifications](file:///d:/Documents/JOCKY/docs/api-contract.md)
- [JOCKY Forensic DSL Specification](file:///d:/Documents/JOCKY/docs/jocky-language.md)
- [Developer Workflow Guide](file:///d:/Documents/JOCKY/docs/development.md)
- [Demo Presentation Script](file:///d:/Documents/JOCKY/docs/demo.md)

---

## Security & Ethics Policy

JOCKY is designed strictly as a defensive, read-only Digital Forensics and Incident Response platform. Offensive capabilities, anti-analysis, AV/EDR evasion, process injection, kernel exploitation, and covert execution are strictly forbidden.
