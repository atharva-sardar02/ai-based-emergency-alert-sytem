# Start Backend API Server
Write-Host "Starting Alexandria Emergency Alert System Backend..." -ForegroundColor Green
Set-Location backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

