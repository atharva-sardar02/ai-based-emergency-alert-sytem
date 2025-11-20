# Start Frontend Server (Optional - Frontend is auto-served by backend)
Write-Host "Starting Frontend Server on port 3000..." -ForegroundColor Green
Write-Host "Note: Frontend is automatically served by the backend at http://localhost:8000" -ForegroundColor Yellow
Write-Host "This script is only needed if you want to run frontend separately" -ForegroundColor Yellow
Set-Location frontend
python -m http.server 3000



