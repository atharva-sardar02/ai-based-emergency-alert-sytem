# Alexandria EAS - Quick Start Guide

## ⚡ Fast Setup (3 minutes)

### 1. Start the Database
```powershell
docker-compose up -d
```
*Wait 10 seconds for PostgreSQL to initialize*

### 2. Start the Backend API
Open a new terminal:
```powershell
.\start-backend.ps1
```

The API will be available at: http://localhost:8000

### 3. Start Ingestion (In another terminal)
```powershell
.\start-ingestion.ps1
```

This will fetch alerts from all sources every 5 minutes.

### 4. Open the Dashboard
Open `frontend/index.html` in your browser, or:
```powershell
cd frontend
python -m http.server 3000
```
Then visit: http://localhost:3000

---

## 🎯 What You'll See

1. **TEST_MODE is ON** (set in `.env`) - Shows Virginia-wide alerts for demonstration
2. **Alerts from multiple sources**: NWS, USGS Earthquakes, River Gauges
3. **AI Classification**: High/Medium/Low criticality (uses rule-based fallback initially)
4. **Interactive UI**: 
   - Click "View More" to see details and acknowledge alerts
   - Click "Not Relevant" to hide alerts from main view

---

## 🔧 Configuration

Edit `.env` file (created automatically):

```env
# Set to false for Alexandria-only alerts
TEST_MODE=true

# Add API keys (optional)
FIRMS_API_KEY=your_key_here
WMATA_API_KEY=your_key_here
```

**Where to get API keys:**
- FIRMS (fire detection): https://firms.modaps.eosdis.nasa.gov/api/area/
- WMATA (transit): https://developer.wmata.com/

---

## 🤖 Enable AI Classification (Optional)

### Install Ollama
1. Download from: https://ollama.ai/
2. Pull the model:
```powershell
ollama pull llama3.2:3b-instruct-q4
```

### Start Classification Worker
```powershell
.\start-classifier.ps1
```

**Without Ollama:** System uses smart rule-based classification (works great!)

---

## 📊 API Endpoints

- `GET http://localhost:8000/api/health` - Health check
- `GET http://localhost:8000/api/alerts` - List alerts
- `GET http://localhost:8000/api/alerts/{id}` - Alert details
- `POST http://localhost:8000/api/alerts/{id}/acknowledge` - Acknowledge alert
- `POST http://localhost:8000/api/alerts/{id}/not-relevant` - Mark as not relevant

Swagger docs: http://localhost:8000/docs

---

## 🔍 Troubleshooting

### Database Connection Error
```powershell
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres
```

### No Alerts Appearing
1. Check ingestion is running (see terminal output)
2. Wait 1-2 minutes for first fetch
3. Check logs for API errors

### Frontend Not Loading Alerts
1. Ensure backend is running: http://localhost:8000/api/health
2. Check browser console for CORS errors
3. Verify API_BASE in `frontend/index.html` is `http://localhost:8000/api`

---

## 🎬 Demo Mode

Want to show the system working with guaranteed data?

1. Keep `TEST_MODE=true` in `.env`
2. System fetches:
   - Virginia-wide NWS alerts
   - Global earthquakes M4.5+
   - River gauges for Potomac region

---

## 🚀 Next Steps

1. ✅ System is running
2. 📍 Switch to production mode: `TEST_MODE=false` in `.env`
3. 🔑 Add FIRMS_API_KEY for fire detection
4. 🤖 Setup Ollama for AI classification
5. 📱 Customize frontend styling
6. 🔔 Add more data sources

---

## 📝 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # Database models
│   │   ├── routers/             # API endpoints
│   │   └── services/            # Ingestion & classification
│   └── alembic/                 # Database migrations
├── frontend/
│   └── index.html               # Dashboard UI
├── docker-compose.yml           # PostgreSQL
└── .env                         # Configuration
```

---

## 🛠️ Development Commands

```powershell
# Create new database migration
cd backend
.\venv\Scripts\Activate.ps1
alembic revision --autogenerate -m "description"
alembic upgrade head

# Test individual source
python -m app.services.ingest_nws
python -m app.services.ingest_usgs_eq

# Reset database
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

---

## ✅ Success Criteria

- [x] API responds at http://localhost:8000/api/health
- [x] Database tables created
- [x] Ingestion fetching alerts
- [x] Dashboard shows alerts
- [x] Can click "View More" and see details
- [x] Can mark alerts as "Not Relevant"
- [x] Can acknowledge alerts

**You're ready to go! 🎉**

