# Database Migrations

This directory will store database migration scripts (managed via Alembic / SQLAlchemy).

### Workflow:
1. Initialize Alembic: `alembic init -t async migrations`
2. Generate migration: `alembic revision --autogenerate -m "create initial tables"`
3. Apply migration: `alembic upgrade head`
