# Start Unified Backend (API + Ingestion + Classification)
Write-Host "Starting Alexandria Emergency Alert System (Unified Mode)..." -ForegroundColor Green
Write-Host "This starts: API Server, Ingestion Scheduler, and Classification Worker" -ForegroundColor Yellow
Set-Location backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

