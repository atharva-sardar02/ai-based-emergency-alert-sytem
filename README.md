# Alexandria Emergency Alert System

Real-time emergency alert system for the City of Alexandria, integrating data from multiple public sources (NWS, USGS, NASA, WMATA) with AI-powered criticality classification.

![System Status](https://img.shields.io/badge/status-production%20ready-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [System Architecture](#-system-architecture)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## ✨ Features

### Multi-Source Data Ingestion
- **NWS Weather Alerts**: Real-time weather warnings, watches, and advisories
- **USGS Earthquakes**: Seismic activity monitoring with magnitude filtering
- **USGS NWIS**: River gauge data for flood monitoring
- **NASA FIRMS**: Satellite-based fire and thermal anomaly detection
- **WMATA**: Metro transit incident alerts

### Intelligent Alert Management
- **AI Classification**: Automatic criticality assessment (High/Medium/Low) using LLM
- **Smart Deduplication**: Prevents duplicate alerts using natural key generation
- **User Actions**: Mark alerts as irrelevant or acknowledge with notes
- **Real-time Updates**: Dashboard auto-refreshes every 60 seconds

### Beautiful Dashboard
- **Modern UI**: Clean, responsive interface with color-coded criticality badges
- **Interactive**: View details, acknowledge alerts, hide irrelevant items
- **Detail Modal**: Full alert information with AI classification rationale
- **Map View**: Interactive map with alert locations and filtering
- **Test Mode**: Virginia-wide alerts for demonstrations

### Interactive Map Visualization
- **Leaflet.js Integration**: Interactive map with zoom and pan controls
- **Location Plotting**: Alerts displayed as markers with coordinates
- **Smart Markers**: Color-coded by criticality (Red/Orange/Yellow)
- **Source Icons**: Custom icons for different alert sources (NWS, USGS, etc.)
- **Filtering**: Filter by source and criticality level
- **Auto-fit Bounds**: Map automatically adjusts to show all visible alerts
- **Real-time Updates**: Map refreshes every 60 seconds with new data

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** (optional) - [Download](https://git-scm.com/)

### Installation (5 minutes)

#### 1. Clone or Download Repository

```bash
git clone https://github.com/yourusername/ai-based-emergency-alert-system.git
cd ai-based-emergency-alert-system
```

#### 2. Create Environment Configuration

Create `backend/.env` file:

```env
# Database
DATABASE_URL=postgresql://eas_user:eas_password@localhost:5432/alexandria_eas

# API Keys (optional but recommended)
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

#### 3. Start Database

```bash
docker-compose up -d
```

*Wait 10 seconds for PostgreSQL to initialize*

#### 4. Install Python Dependencies

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

#### 5. Run Database Migrations

```bash
alembic upgrade head
```

#### 6. Start the Backend API

```bash
uvicorn app.main:app --reload --port 8000
```

**Keep this terminal running!** The API is now available at http://localhost:8000

#### 7. Run Initial Data Ingestion (New Terminal)

```bash
cd backend
.\venv\Scripts\Activate.ps1  # or source venv/bin/activate

python -m app.services.ingest_nws
python -m app.services.ingest_usgs_eq
python -m app.services.ingest_nwis
```

#### 8. Start Classification Worker (New Terminal)

```bash
cd backend
.\venv\Scripts\Activate.ps1  # or source venv/bin/activate

python -m app.services.classify
```

#### 9. Start Frontend Server (New Terminal)

```bash
cd frontend
python -m http.server 3000
```

#### 10. Open Dashboard

Visit: **http://localhost:3000**

🎉 **You should now see your emergency alerts!**

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Dashboard)                      │
│  • View alerts with criticality badges                      │
│  • Click "Know More" for details                            │
│  • Mark alerts as "Irrelevant" (moves to bottom)            │
│  • Acknowledge alerts with notes                            │
└──────────────────┬──────────────────────────────────────────┘
                   │ REST API (HTTP)
┌──────────────────▼──────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  • GET /api/alerts - List all alerts                        │
│  • GET /api/alerts/{id} - Alert details                     │
│  • POST /api/alerts/{id}/not-relevant                       │
│  • POST /api/alerts/{id}/acknowledge                        │
└─────┬─────────────────────┬─────────────────────┬──────────┘
      │                     │                     │
┌─────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  INGESTION   │  │ CLASSIFICATION  │  │   DEDUPLICATION │
│   SERVICE    │  │     SERVICE     │  │     SERVICE     │
│              │  │                 │  │                 │
│ • NWS        │  │ • LLM (Ollama) │  │ • SHA256 hash   │
│ • USGS EQ    │  │ • Rule fallback│  │ • Unique index  │
│ • NWIS       │  │ • High/Med/Low │  │ • Prevents dupes│
│ • FIRMS      │  │                 │  │                 │
│ • WMATA      │  │                 │  │                 │
└─────┬────────┘  └────────┬────────┘  └────────┬────────┘
      │                    │                     │
      └────────────────────┼─────────────────────┘
                           │
                  ┌────────▼────────┐
                  │   PostgreSQL    │
                  │    Database     │
                  │                 │
                  │ • alerts        │
                  │ • classifications│
                  │ • user_actions  │
                  └─────────────────┘
```

---

## 📖 API Documentation

### Interactive Documentation

Visit http://localhost:8000/docs for full Swagger/OpenAPI documentation.

### Key Endpoints

#### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-15T17:00:00",
  "version": "0.1.0"
}
```

#### `GET /api/alerts`
List all alerts with pagination and filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 50, max: 100)
- `criticality` (str): Filter by High/Medium/Low
- `show_irrelevant` (bool): Include hidden alerts (default: false)

**Response:**
```json
{
  "alerts": [...],
  "total": 150,
  "page": 1,
  "limit": 50,
  "has_more": true
}
```

#### `GET /api/alerts/{id}`
Get detailed information about a specific alert.

**Response:**
```json
{
  "id": 123,
  "title": "Winter Storm Warning",
  "summary": "Heavy snow expected...",
  "source": "NWS",
  "event_type": "Winter Weather",
  "severity": "Severe",
  "urgency": "Immediate",
  "area": "Alexandria, VA",
  "effective_at": "2025-10-15T18:00:00Z",
  "url": "https://...",
  "latest_classification": {
    "criticality": "High",
    "rationale": "Severe weather with immediate urgency",
    "model_version": "llama3.2-3b"
  },
  "user_actions": [],
  "raw_payload": "{...}"
}
```

#### `POST /api/alerts/{id}/not-relevant`
Mark an alert as not relevant (hides from main view).

**Response:**
```json
{
  "message": "Alert marked as not relevant",
  "action_id": 456,
  "alert_id": 123
}
```

#### `POST /api/alerts/{id}/acknowledge`
Acknowledge an alert with optional note.

**Request Body:**
```json
{
  "note": "Assigned to Fire Department. Monitoring situation."
}
```

**Response:**
```json
{
  "message": "Alert acknowledged",
  "action_id": 789,
  "alert_id": 123,
  "note": "Assigned to Fire Department..."
}
```

---

## ⚙️ Configuration

### Environment Variables

Edit `backend/.env` to configure the system:

#### Database
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

#### Test Mode
```env
TEST_MODE=true   # Virginia-wide alerts for demos
TEST_MODE=false  # Alexandria-only (production)
```

#### Data Refresh Rate
```env
REFRESH_INTERVAL_SECONDS=300  # Fetch new data every 5 minutes
```

#### API Keys

Get free API keys for enhanced functionality:

**NASA FIRMS** (Fire Detection)
- Visit: https://firms.modaps.eosdis.nasa.gov/api/area/
- Sign up (free, instant)
- Add to `.env`: `FIRMS_API_KEY=your_key_here`

**WMATA** (Transit Alerts)
- Visit: https://developer.wmata.com/
- Create account and subscribe to Default Tier (free)
- Add to `.env`: `WMATA_API_KEY=your_key_here`

### Geographic Scope

**Production Mode** (TEST_MODE=false):
- NWS: Alexandria point-based query
- USGS EQ: 10km radius from Alexandria City Hall
- FIRMS: Alexandria bounding box

**Test Mode** (TEST_MODE=true):
- NWS: Virginia state-wide
- USGS EQ: Global earthquakes M4.5+
- FIRMS: Better coverage for demonstrations

---

## 🛠️ Development

### Project Structure

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
│   │   │   ├── ingest_fires.py
│   │   │   ├── ingest_scheduler.py
│   │   │   └── classify.py
│   │   └── utils/
│   │       ├── dedupe.py
│   │       └── time_utils.py
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt         # Dependencies
│   └── .env                     # Configuration
├── frontend/
│   ├── index.html               # Dashboard UI (List View)
│   └── map.html                 # Map View with Leaflet.js
├── docker-compose.yml           # PostgreSQL setup
└── README.md                    # This file
```

### Running Services

#### Continuous Ingestion
```bash
cd backend
python -m app.services.ingest_scheduler
```
Automatically fetches new data every 5 minutes.

#### Classification Worker
```bash
cd backend
python -m app.services.classify
```
Continuously classifies new unclassified alerts.

#### Manual Ingestion (Testing)
```bash
# Test individual sources
python -m app.services.ingest_nws
python -m app.services.ingest_usgs_eq
python -m app.services.ingest_nwis
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Adding a New Data Source

1. Create `backend/app/services/ingest_newsource.py`
2. Inherit from `BaseIngestionService`
3. Implement `fetch_raw_data()` and `normalize_item()`
4. Add to scheduler in `ingest_scheduler.py`

Example:
```python
from app.services.ingest_base import BaseIngestionService

class IngestNewSource(BaseIngestionService):
    def __init__(self, db_session):
        super().__init__(db_session)
        self.source_name = "NewSource"
    
    async def fetch_raw_data(self):
        # Fetch from API
        pass
    
    def normalize_item(self, raw_item):
        # Convert to standard format
        pass
```

---

## 🔧 Troubleshooting

### API Returns "Not Found"

**Problem:** Multiple servers running on port 8000

**Solution:**
```bash
# Windows
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force

# Linux/Mac
killall python

# Then restart the server
uvicorn app.main:app --reload --port 8000
```

### Database Connection Failed

**Check Docker:**
```bash
docker-compose ps
docker-compose logs postgres
```

**Restart Database:**
```bash
docker-compose down
docker-compose up -d
# Wait 10 seconds
alembic upgrade head
```

### Frontend Shows CORS Error

**Problem:** Opening `index.html` directly as `file://`

**Solution:** Use HTTP server
```bash
cd frontend
python -m http.server 3000
# Visit http://localhost:3000
```

### No Alerts Appearing

1. **Check ingestion ran:**
   ```bash
   python -m app.services.ingest_nws
   ```
   Should show: "Ingested X new NWS alerts"

2. **Check database:**
   ```bash
   # In psql or pgAdmin
   SELECT COUNT(*) FROM alerts;
   ```

3. **Enable TEST_MODE** in `.env` for guaranteed data:
   ```env
   TEST_MODE=true
   ```

### LLM Classification Not Working

System falls back to rule-based classification automatically.

**To enable LLM:**
1. Install Ollama: https://ollama.ai/
2. Pull model: `ollama pull llama3.2:3b-instruct-q4`
3. Restart classification worker

---

## 🎯 Production Deployment

### Recommended Stack

- **Backend**: Railway, Render, or AWS EC2
- **Database**: AWS RDS PostgreSQL or Supabase
- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **LLM**: Self-hosted Ollama or cloud API (OpenAI, Anthropic)

### Environment Setup

1. Update `DATABASE_URL` to production database
2. Set `TEST_MODE=false`
3. Configure production CORS origins
4. Add SSL certificates
5. Set up monitoring (Sentry, DataDog)

### Security Checklist

- ✅ Never commit `.env` files
- ✅ Use strong database passwords
- ✅ Enable HTTPS only
- ✅ Implement rate limiting
- ✅ Add user authentication (future)
- ✅ Regular security updates

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8
- **JavaScript**: Use ES6+ features
- **Commits**: Use conventional commits format

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **National Weather Service** for weather alert data
- **USGS** for earthquake and river gauge data
- **NASA** for FIRMS fire detection
- **WMATA** for transit incident data
- **City of Alexandria** for emergency management collaboration

---

## 📞 Support

- **Documentation**: See `QUICKSTART.md`, `SETUP_INSTRUCTIONS.md`, `API_KEYS_INFO.md`
- **Issues**: Open an issue on GitHub
- **Email**: support@alexandria-eas.org

---

## 🗺️ Roadmap

### Version 0.2 (Next)
- [ ] User authentication and roles
- [x] Map visualization with alert locations
- [ ] Email/SMS notifications
- [ ] Mobile responsive improvements

### Version 0.3 (Future)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Integration with 911 CAD systems
- [ ] Multi-jurisdictional support

---

**Built with ❤️ for the City of Alexandria Emergency Management**
