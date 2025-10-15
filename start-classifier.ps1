# Start Classification Worker
Write-Host "Starting Alert Classification Worker..." -ForegroundColor Green
Write-Host "Note: Requires Ollama running with llama3.2:3b-instruct-q4 model" -ForegroundColor Yellow
Write-Host "Falls back to rule-based classification if LLM unavailable" -ForegroundColor Yellow
Set-Location backend
.\venv\Scripts\Activate.ps1
python -m app.services.classify

