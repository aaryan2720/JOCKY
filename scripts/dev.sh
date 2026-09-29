#!/usr/bin/env bash
set -e

echo "=================================================="
echo " Starting JOCKY Local Development Environment"
echo "=================================================="

# Function to clean up background processes on exit
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Start Backend
echo "Starting Backend (FastAPI on :8000)..."
(cd backend && uvicorn app.main:app --reload --port 8000) &

# Start Frontend
echo "Starting Frontend (Vite on :5173)..."
(cd frontend && npm run dev) &

# Wait for all background processes
wait
