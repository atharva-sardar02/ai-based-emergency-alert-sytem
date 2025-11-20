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

**Unified Mode (Recommended)**: One command starts everything!

```powershell
# From project root - starts API, Ingestion, Classification, AND Frontend
./start-backend.ps1
```

That's it! The unified backend automatically:
- Starts the API server on port 8000
- Starts the ingestion scheduler (fetches all sources every 5 minutes)
- Starts the classification worker (processes alerts continuously)
- **Serves the frontend automatically at http://localhost:8000**

**No separate frontend server needed!** The frontend is served directly by FastAPI.

### Frontend Options

**Option 1: Automatic (Recommended)**
- Frontend is automatically served when you run `./start-backend.ps1`
- Access at: http://localhost:8000
- No additional steps needed

**Option 2: Separate Frontend Server (Optional)**
If you prefer to run the frontend separately (e.g., for development/debugging):

```powershell
# In a separate terminal
cd frontend
python -m http.server 3000
```

Then access at: http://localhost:3000

**Alternative**: If you prefer separate processes for debugging, you can still run:
- `./start-backend.ps1` - API + Ingestion + Classification (frontend included)
- `./start-ingestion.ps1` - Ingestion scheduler only
- `./start-classifier.ps1` - Classification worker only

The dashboard will automatically keep updating with alerts from:
- NWS Weather, USGS Earthquakes, USGS NWIS (no keys required)
- NASA FIRMS (fires) and WMATA (transit) if keys are present in root `.env`

## Where to open

**With Unified Mode (Recommended)**:
- **Dashboard**: http://localhost:8000 (automatically served by FastAPI)
- **Map View**: http://localhost:8000/map.html
- **API docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/api/health

**With Separate Frontend Server**:
- **Dashboard**: http://localhost:3000
- **Map View**: http://localhost:3000/map.html
- **API docs**: http://localhost:8000/docs (still on backend port)

## Notes

- Ensure root `.env` file exists (one level up from `backend/`). Keys are optional:
  - `OPENAI_API_KEY=` (optional, for OpenAI classification)
  - `FIRMS_API_KEY=` (optional)
  - `WMATA_API_KEY=` (optional)
- Set `TEST_MODE=true` for Virginia-wide demo coverage.
- The unified backend runs all services in a single process for simplicity.

## Stop everything
Press Ctrl+C in each terminal. To stop Postgres:
```powershell
docker-compose down
```

