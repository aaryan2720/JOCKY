# JOCKY Developer Guide & Workflow

## 1. Prerequisites

- **Node.js**: v18+ (tested on v20/v22) and npm
- **Python**: 3.10+ (tested on Python 3.11)
- **Go**: 1.21+ (for agent development and cross-compilation)
- **Docker & Docker Compose**: for containerized databases and services
- **Git**

---

## 2. Independent 2-Developer Split Workflow

The monorepo structure is designed to allow two developers to work concurrently with clean module ownership:

```
+-------------------------------------------------------------+
| Developer A (UI & Web Services)                             |
|  - frontend/ (React, Vite, Tailwind, UI features)           |
|  - backend/app/api/ (REST routes & WebSockets)              |
|  - backend/app/schemas/ (API DTOs & Validation)             |
|  - backend/app/models/ & db/ (Persistence layer)            |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
| Developer B (Forensic Engine & Core Systems)                |
|  - agent/ (Go collectors, runtime, transport, detection)    |
|  - backend/app/jocky/ (Lexer, Parser, AST, Planner)         |
|  - backend/app/orchestration/ & detection/ (Correlation)    |
|  - rules/ (YARA, Sigma rule sets)                           |
+-------------------------------------------------------------+
```

---

## 3. Quickstart Commands

### Setup Environment
```bash
cp .env.example .env
```

### Option A: Local Native Execution (Recommended for Fast Dev)
```bash
# Terminal 1: Backend
cd backend
python -m venv .venv
source .venv/bin/activate # or .venv\Scripts\Activate on Windows
pip install -r requirements.txt # or pip install -e .
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Terminal 3: Go Agent
cd agent
go run cmd/agent/main.go
```

### Option B: Docker Compose
```bash
# Start PostgreSQL & Redis
docker compose up -d postgres redis

# Verify Health
curl http://localhost:8000/health
```

---

## 4. Testing & Verification

```bash
# Run all tests
make test

# Individual suites
make test-backend
make test-frontend
make test-agent
```
