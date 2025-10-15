# Start Ingestion Scheduler
Write-Host "Starting Alert Ingestion Scheduler..." -ForegroundColor Green
Set-Location backend
.\venv\Scripts\Activate.ps1
python -m app.services.ingest_scheduler

