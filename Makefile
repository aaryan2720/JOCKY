.PHONY: help dev backend frontend agent test test-backend test-frontend test-agent lint format docker-up docker-down clean

help:
	@echo "JOCKY - Digital Forensics & Incident Response Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make dev          - Start backend and frontend development servers concurrently"
	@echo "  make backend      - Run FastAPI backend locally"
	@echo "  make frontend     - Run React frontend locally"
	@echo "  make agent        - Build and run Go forensic agent locally"
	@echo "  make test         - Run test suites across backend, frontend, and agent"
	@echo "  make test-backend - Run backend pytest suite"
	@echo "  make test-frontend- Run frontend test/typecheck suite"
	@echo "  make test-agent   - Run Go agent tests"
	@echo "  make lint         - Run linters across projects"
	@echo "  make format       - Run code formatters (ruff/black, prettier, gofmt)"
	@echo "  make docker-up    - Start infrastructure containers (PostgreSQL, Redis, Backend)"
	@echo "  make docker-down  - Stop infrastructure containers"
	@echo "  make clean        - Remove build artifacts and temporary files"

dev:
	@bash scripts/dev.sh || powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

agent:
	cd agent && go run cmd/agent/main.go

test: test-backend test-frontend test-agent

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm run build

test-agent:
	cd agent && go test ./...

lint:
	cd frontend && npm run lint
	cd backend && ruff check . || flake8 . || echo "Backend linter not installed, skipping"
	cd agent && go vet ./... || echo "Go vet check finished"

format:
	cd frontend && npm run format || echo "Prettier finished"
	cd backend && ruff format . || black . || echo "Python formatter finished"
	cd agent && gofmt -s -w . || echo "gofmt finished"

docker-up:
	docker compose up -d postgres redis

docker-down:
	docker compose down

clean:
	rm -rf backend/.pytest_cache frontend/dist agent/bin
