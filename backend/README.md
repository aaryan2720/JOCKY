# JOCKY Backend & Language Engine

The **JOCKY Backend** is a high-performance FastAPI management server responsible for fleet coordination, JOCKY DSL compilation, job orchestration, forensic evidence persistence, and threat detection correlation.

---

## Directory Organization

- `app/api/`: REST endpoints (`/api/v1/*`) and WebSocket handlers (`/ws/*`).
- `app/core/`: Configuration, application lifecycle, security, and global settings.
- `app/db/`: SQLAlchemy async session management and base declarative model.
- `app/models/`: SQLAlchemy ORM database models.
- `app/schemas/`: Pydantic request and response schemas (DTOs).
- `app/services/`: Reusable business logic separated from HTTP controllers.
- `app/orchestration/`: Job creation, agent targeting, and dispatch logic.
- `app/detection/`: Rule matching and evidence correlation engine.
- `app/jocky/`: Isolated JOCKY DSL language pipeline (Lexer, Parser, AST, Interpreter, Planner).

---

## Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
```

---

## Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "ok",
  "service": "jocky-backend"
}
```
