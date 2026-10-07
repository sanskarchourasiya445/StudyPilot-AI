# =============================================================================
# run_dev.ps1 - Launch StudyPilot AI Local Development Stack (Windows)
# =============================================================================

$ProjectRoot = $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Starting StudyPilot AI Local Dev Stack  " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Launch Backend Server in a new window
Write-Host "`n[1/2] Launching FastAPI Backend (http://localhost:8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; Write-Host '--- StudyPilot FastAPI Backend ---' -ForegroundColor Green; .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

# 2. Launch Frontend Dev Server in a new window
Write-Host "[2/2] Launching React/Vite Frontend (http://localhost:5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\frontend'; Write-Host '--- StudyPilot React Frontend ---' -ForegroundColor Cyan; npm run dev"

Write-Host "`n[SUCCESS] Both servers launched in separate windows!" -ForegroundColor Yellow
Write-Host "  - Frontend URL:  http://localhost:5173" -ForegroundColor White
Write-Host "  - Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  - Swagger Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "==========================================`n" -ForegroundColor Cyan
