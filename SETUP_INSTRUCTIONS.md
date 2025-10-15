# Alexandria Emergency Alert System - Setup Instructions

## ✅ What Has Been Built

I've created a complete MVP emergency alert system with:

### Backend (FastAPI + PostgreSQL)
- ✅ Database models for Alerts, Classifications, and User Actions
- ✅ RESTful API endpoints for alert management
- ✅ Multi-source data ingestion (NWS, USGS Earthquakes, USGS NWIS)
- ✅ AI classification service with rule-based fallback
- ✅ Automatic deduplication using natural keys
- ✅ Scheduled ingestion every 5 minutes

### Frontend
- ✅ Modern, beautiful dashboard UI
- ✅ Real-time alert display with criticality badges
- ✅ Detail modal for viewing full alert information
- ✅ Action buttons (View More, Not Relevant, Acknowledge)
- ✅ Auto-refresh every 60 seconds

### Infrastructure
- ✅ Docker Compose for PostgreSQL
- ✅ Alembic database migrations
- ✅ Helper scripts for easy startup

---

## 🔧 Manual Setup Steps

### Step 1: Create .env File

Create a file named `.env` in the `backend` directory with this content:

```env
# Database
DATABASE_URL=postgresql://eas_user:eas_password@localhost:5432/alexandria_eas

# API Keys (optional)
FIRMS_API_KEY=
WMATA_API_KEY=

# LLM Configuration
MODEL_NAME=llama3.2:3b-instruct-q4
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
TEST_MODE=true
REFRESH_INTERVAL_SECONDS=300
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:3000
```

**Path:** `backend/.env`

### Step 2: Verify Database is Running

```powershell
docker-compose ps
```

Should show `alexandria_eas_db` as running.

### Step 3: Start the Backend API

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Test:** Open http://localhost:8000/api/health in your browser

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "database": "connected",
  "version": "0.1.0"
}
```

### Step 4: Run Initial Data Ingestion

Open a new terminal:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m app.services.ingest_nws
python -m app.services.ingest_usgs_eq
python -m app.services.ingest_nwis
```

This will fetch alerts from all sources immediately.

### Step 5: Start Classification

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m app.services.classify
```

Leave this running to classify new alerts (uses rule-based classification by default).

### Step 6: Start Continuous Ingestion (Optional)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m app.services.ingest_scheduler
```

This will fetch new alerts every 5 minutes automatically.

### Step 7: Open the Dashboard

Simply open `frontend/index.html` in your web browser!

Or serve it with:
```powershell
cd frontend
python -m http.server 3000
```

Then visit: http://localhost:3000

---

## 📊 Testing the System

### 1. Check API Endpoints

```powershell
# Health check
Invoke-RestMethod http://localhost:8000/api/health

# List alerts
Invoke-RestMethod http://localhost:8000/api/alerts

# View documentation
# Open: http://localhost:8000/docs
```

### 2. Test Frontend Actions

1. **View Alerts**: Should see alerts from NWS, USGS, etc.
2. **Click "View More"**: Opens detail modal with full information
3. **Click "Not Relevant"**: Removes alert from main list
4. **Acknowledge**: Add a note and acknowledge an alert

### 3. Verify Data Sources

With `TEST_MODE=true` (in `.env`), you should see:
- **NWS Alerts**: Virginia-wide weather alerts
- **USGS Earthquakes**: Global earthquakes M4.5+
- **USGS NWIS**: Potomac River gauge readings

---

## 🔑 Adding API Keys (Optional but Recommended)

### NASA FIRMS (Fire Detection)

1. Visit: https://firms.modaps.eosdis.nasa.gov/api/area/
2. Sign up for a free API key
3. Add to `backend/.env`:
   ```env
   FIRMS_API_KEY=your_key_here
   ```

### WMATA (Transit Alerts)

1. Visit: https://developer.wmata.com/
2. Create account and get API key
3. Add to `backend/.env`:
   ```env
   WMATA_API_KEY=your_key_here
   ```

**Restart the backend after adding keys!**

---

## 🤖 Enable AI Classification (Optional)

### Install Ollama

1. Download from: https://ollama.ai/download
2. Install and run Ollama
3. Pull the model:

```powershell
ollama pull llama3.2:3b-instruct-q4
```

4. Restart the classification worker

The system will automatically use the LLM for classification. If LLM is unavailable, it falls back to smart rule-based classification.

---

## 🎬 Switch to Production Mode

For Alexandria-only alerts (instead of Virginia-wide):

Edit `backend/.env`:
```env
TEST_MODE=false
```

Restart the backend and ingestion services.

---

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Database models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── database.py          # DB connection
│   │   ├── settings.py          # Configuration
│   │   ├── routers/
│   │   │   └── alerts.py        # API endpoints
│   │   ├── services/
│   │   │   ├── ingest_nws.py
│   │   │   ├── ingest_usgs_eq.py
│   │   │   ├── ingest_nwis.py
│   │   │   ├── ingest_scheduler.py
│   │   │   └── classify.py
│   │   └── utils/
│   │       ├── dedupe.py
│   │       └── time_utils.py
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt         # Dependencies
│   └── .env                     # Configuration (CREATE THIS!)
├── frontend/
│   └── index.html               # Dashboard UI
├── docker-compose.yml           # PostgreSQL
├── .env.example                 # Template
├── README.md                    # Full documentation
├── QUICKSTART.md                # Quick reference
└── start-*.ps1                  # Helper scripts
```

---

## 🐛 Troubleshooting

### API Returns 404

- Check that `.env` exists in `backend/` directory
- Verify DATABASE_URL is correct
- Restart the backend server

### No Alerts Appearing

1. Run manual ingestion first:
   ```powershell
   python -m app.services.ingest_nws
   ```
2. Check for errors in terminal output
3. Verify `TEST_MODE=true` for guaranteed data

### Frontend Doesn't Load Alerts

1. Check backend is running: http://localhost:8000/api/alerts
2. Open browser console (F12) and check for errors
3. Verify CORS settings in `backend/.env`

### Database Connection Failed

```powershell
docker-compose down
docker-compose up -d
# Wait 10 seconds
cd backend
alembic upgrade head
```

---

## ✅ Success Checklist

- [ ] PostgreSQL running (`docker-compose ps`)
- [ ] Backend API running (http://localhost:8000/api/health shows "healthy")
- [ ] Database tables created (`alembic upgrade head`)
- [ ] At least one ingestion completed
- [ ] Frontend loads and shows alerts
- [ ] Can click "View More" on an alert
- [ ] Can mark alerts as "Not Relevant"
- [ ] Can acknowledge alerts with notes

---

## 🚀 Next Steps

1. **Add API Keys**: Get FIRMS and WMATA keys for complete data
2. **Install Ollama**: Enable AI-powered classification
3. **Customize**: Modify frontend styling and branding
4. **Deploy**: Move to production server
5. **Add Sources**: Integrate additional data sources
6. **Add Auth**: Implement user authentication

---

## 📞 API Reference

### GET /api/alerts
List alerts with pagination and filtering

Query parameters:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)
- `criticality`: Filter by High/Medium/Low
- `show_irrelevant`: Include hidden alerts (default: false)

### GET /api/alerts/{id}
Get detailed alert information including raw payload

### POST /api/alerts/{id}/not-relevant
Mark an alert as not relevant (moves to bottom)

### POST /api/alerts/{id}/acknowledge
Acknowledge an alert with optional note

Body:
```json
{
  "note": "Assigned to Fire Department. Monitoring situation."
}
```

**Full API Documentation:** http://localhost:8000/docs

---

## 🎉 You're All Set!

The system is ready to use. Start with the manual setup steps above, and you'll have a fully functional emergency alert system in about 5-10 minutes.

For quick reference, see `QUICKSTART.md`.

Questions? Check `README.md` for detailed documentation.

