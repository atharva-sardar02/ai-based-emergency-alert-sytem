# 🚀 How to Run Alexandria EAS Locally (Minimal Steps)

## One-time setup (first run only)

```powershell
# 1) Start PostgreSQL
docker-compose up -d

# 2) Create virtualenv and install deps
cd backend
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt

# 3) Run DB migrations
alembic upgrade head
```

## Start everything (every run)

Open three terminals and run these scripts from the project root:

```powershell
# Terminal A - API server
./start-backend.ps1
```
```powershell
# Terminal B - Ingestion scheduler (ALL SOURCES, continuous)
./start-ingestion.ps1
```
```powershell
# Terminal C - Classification worker (AI with rules fallback)
./start-classifier.ps1
```
```powershell
# Terminal D - Frontend (serves dashboard at http://localhost:3000)
cd frontend; python -m http.server 3000
```

That’s it. The dashboard will automatically keep updating with alerts from:
- NWS Weather, USGS Earthquakes, USGS NWIS (no keys required)
- NASA FIRMS (fires) and WMATA (transit) if keys are present in `backend/.env`

## Where to open

- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Notes

- Ensure `backend/.env` exists. Keys are optional:
  - `FIRMS_API_KEY=` (optional)
  - `WMATA_API_KEY=` (optional)
- Set `TEST_MODE=true` for Virginia-wide demo coverage.

## Stop everything
Press Ctrl+C in each terminal. To stop Postgres:
```powershell
docker-compose down
```

