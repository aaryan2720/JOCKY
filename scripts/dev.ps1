Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting JOCKY Local Development Environment" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting Backend (FastAPI on :8000)..." -ForegroundColor Green
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn app.main:app --reload --port 8000" -PassThru

Write-Host "Starting Frontend (Vite on :5173)..." -ForegroundColor Green
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -PassThru

Write-Host "Services started." -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000/health"
Write-Host "Docs:     http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:5173"
