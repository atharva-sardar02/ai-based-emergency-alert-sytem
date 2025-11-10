# Technical Context: Technologies & Setup

## Technology Stack

### Backend
- **Python**: 3.10+ (currently using 3.12)
- **Framework**: FastAPI 0.109.0
- **Database ORM**: SQLAlchemy 2.0.25
- **Migrations**: Alembic 1.13.1
- **HTTP Client**: httpx 0.25.2
- **Scheduling**: APScheduler 3.10.4
- **Settings**: pydantic-settings 2.1.0
- **Database Driver**: psycopg2-binary 2.9.9

### Database
- **PostgreSQL**: 16 (via Docker)
- **Connection**: SQLAlchemy with connection pooling
- **Tables**: 3 (alerts, classifications, user_actions)

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling (no framework)
- **JavaScript**: ES6+ (vanilla, no frameworks)
- **HTTP Client**: Fetch API
- **Map Library**: Leaflet.js for interactive maps

### Classification
- **LLM**: Ollama with llama3.2:3b-instruct-q4
- **Connection**: Explicit OLLAMA_BASE_URL from settings
- **Fallback**: Rule-based classification

### Infrastructure
- **Containerization**: Docker Compose
- **Web Server**: Uvicorn (ASGI)
- **Process Management**: Helper scripts (start-*.ps1)

## Database Schema

### Table: alerts
**Purpose**: Store normalized emergency alerts from all sources

**Columns (17 total)**:
- `id` (Integer, PK, indexed)
- `natural_key` (String(255), unique, indexed) - SHA256 hash for deduplication
- `source` (String(100), indexed) - Data source name (NWS, USGS_Earthquakes, etc.)
- `provider_id` (String(255), nullable) - Original ID from source
- `title` (String(500), required) - Alert title
- `summary` (Text, nullable) - Alert summary/description
- `event_type` (String(100), nullable) - Type of event
- `severity` (String(50), nullable) - Severity level
- `urgency` (String(50), nullable) - Urgency level
- `area` (String(500), nullable) - Geographic area description
- `effective_at` (DateTime(timezone=True), required, indexed) - When alert is effective
- `expires_at` (DateTime(timezone=True), nullable) - When alert expires
- `created_at` (DateTime(timezone=True), default now) - When record was created
- `url` (Text, nullable) - Source URL
- `raw_payload` (Text, nullable) - Original JSON as string
- `latitude` (Float, nullable) - Geographic latitude for mapping
- `longitude` (Float, nullable) - Geographic longitude for mapping

**Indexes**:
- `idx_alerts_effective_at` on `effective_at`
- `idx_alerts_source_provider` on `source`, `provider_id`
- `idx_alerts_location` on `latitude`, `longitude`
- Unique constraint on `natural_key`

**Relationships**:
- One-to-many with `classifications`
- One-to-many with `user_actions`

### Table: classifications
**Purpose**: Store AI/rule-based classification results

**Columns (6 total)**:
- `id` (Integer, PK, indexed)
- `alert_id` (Integer, FK → alerts.id, indexed, CASCADE delete)
- `criticality` (String(20), required, indexed) - High, Medium, or Low
- `rationale` (Text, nullable) - Explanation for classification
- `model_version` (String(100), required) - Model name or "rules-fallback"
- `created_at` (DateTime(timezone=True), default now)

**Indexes**:
- `ix_classifications_alert_id` on `alert_id`
- `ix_classifications_criticality` on `criticality`

**Relationships**:
- Many-to-one with `alerts`

### Table: user_actions
**Purpose**: Store user interactions with alerts

**Columns (6 total)**:
- `id` (Integer, PK, indexed)
- `alert_id` (Integer, FK → alerts.id, indexed, CASCADE delete)
- `action` (String(50), required) - "acknowledged" or "irrelevant"
- `note` (Text, nullable) - Optional note from user
- `actor` (String(255), nullable) - Placeholder for future auth
- `created_at` (DateTime(timezone=True), default now)

**Indexes**:
- `idx_user_actions_alert_action` on `alert_id`, `action`

**Relationships**:
- Many-to-one with `alerts`

## Development Environment

### Required Tools
1. **Python 3.10+**
   - Download from https://www.python.org/downloads/
   - Verify: `python --version`

2. **Docker Desktop**
   - Download from https://www.docker.com/products/docker-desktop/
   - Required for PostgreSQL container

3. **Git** (optional)
   - For version control

### Python Environment Setup

**Virtual Environment**:
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

**Dependencies**:
```bash
pip install -r requirements.txt
```

**Key Dependencies**:
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `sqlalchemy` - ORM
- `alembic` - Migrations
- `httpx` - HTTP client
- `apscheduler` - Task scheduling
- `pydantic` - Data validation
- `pydantic-settings` - Settings management
- `psycopg2-binary` - PostgreSQL driver
- `python-dotenv` - Environment variables
- `ollama` - LLM client

## Database Setup

### Docker Compose

**File**: `docker-compose.yml`

**Services**:
- PostgreSQL 16 on port 5432
- Default credentials: `eas_user` / `eas_password`
- Database: `alexandria_eas`
- Persistent volume: `postgres_data`

**Start Database**:
```bash
docker-compose up -d
```

**Verify**:
```bash
docker-compose ps
```

### Database Migrations

**Initialize** (first time):
```bash
cd backend
alembic upgrade head
```

**Create Migration**:
```bash
alembic revision --autogenerate -m "description"
```

**Apply Migrations**:
```bash
alembic upgrade head
```

**Rollback**:
```bash
alembic downgrade -1
```

## Configuration

### Environment Variables

**File**: `backend/.env`

**Required**:
```env
DATABASE_URL=postgresql://eas_user:eas_password@localhost:5432/alexandria_eas
```

**Optional** (API Keys):
```env
FIRMS_API_KEY=your_firms_key
WMATA_API_KEY=your_wmata_key
```

**Optional** (LLM):
```env
MODEL_NAME=llama3.2:3b-instruct-q4
OLLAMA_BASE_URL=http://localhost:11434
```

**Application Settings**:
```env
TEST_MODE=true  # or false for production
REFRESH_INTERVAL_SECONDS=300  # 5 minutes
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Settings Management

**File**: `app/settings.py`

- Uses Pydantic Settings for type-safe configuration
- Loads from `.env` file automatically
- Validates on startup
- Provides defaults for optional settings
- CORS_ORIGINS parsed from comma-separated string

**Geographic Configuration**:
- Alexandria center coordinates (38.8048, -77.0469)
- Bounding box for area queries
- Radius for earthquake detection (10km production, global test)

## Running the System

### Service Startup Order (Simplified with Scripts)

1. **Database** (Terminal 1, one-time):
```bash
docker-compose up -d
# Wait 10 seconds for initialization
```

2. **Backend API** (Terminal 2):
```bash
./start-backend.ps1
# Or manually:
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

3. **Ingestion Scheduler** (Terminal 3):
```bash
./start-ingestion.ps1
# Or manually:
cd backend
.\venv\Scripts\Activate.ps1
python -m app.services.ingest_scheduler
```

4. **Classification Worker** (Terminal 4):
```bash
./start-classifier.ps1
# Or manually:
cd backend
.\venv\Scripts\Activate.ps1
python -m app.services.classify
```

5. **Frontend** (Terminal 5, or just open file):
```bash
cd frontend
python -m http.server 3000
# Or simply open index.html in browser
```

### Helper Scripts (Windows)

- `start-backend.ps1` - Start API server
- `start-ingestion.ps1` - Run continuous ingestion (all sources)
- `start-classifier.ps1` - Start classification worker

## API Endpoints

### Base URL
- Local: `http://localhost:8000`
- API Prefix: `/api`

### Key Endpoints

**Health Check**:
- `GET /api/health`
- Returns system status and database connection state

**List Alerts**:
- `GET /api/alerts?page=1&limit=50&criticality=High&show_irrelevant=false`
- Paginated alert listing
- Supports filtering by criticality
- Can show/hide irrelevant alerts

**Alert Details**:
- `GET /api/alerts/{id}`
- Full alert information including raw payload

**User Actions**:
- `POST /api/alerts/{id}/not-relevant`
- `POST /api/alerts/{id}/acknowledge` (with optional note in body)

**Interactive Docs**:
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## API Keys & External Services

### Required: None
System works without any API keys using free/public endpoints.

### Optional: NASA FIRMS
- **Purpose**: Fire detection
- **Cost**: Free
- **Setup**: Sign up at https://firms.modaps.eosdis.nasa.gov/api/area/
- **Add**: `FIRMS_API_KEY=your_key` to `.env`
- **Behavior**: Gracefully skipped if key missing

### Optional: WMATA
- **Purpose**: Transit alerts
- **Cost**: Free (Default Tier)
- **Setup**: Register at https://developer.wmata.com/
- **Add**: `WMATA_API_KEY=your_key` to `.env`
- **Behavior**: Gracefully skipped if key missing

### Optional: Ollama
- **Purpose**: AI classification
- **Cost**: Free (local execution)
- **Setup**: Download from https://ollama.ai/
- **Start**: `ollama serve` (or use desktop app)
- **Pull Model**: `ollama pull llama3.2:3b-instruct-q4`
- **Connection**: Uses `OLLAMA_BASE_URL` from settings (default: http://localhost:11434)
- **Fallback**: Rule-based classification works without Ollama

## Data Sources

### NWS (National Weather Service)
- **Endpoint**: Public API
- **Data**: Weather alerts, watches, advisories
- **Format**: GeoJSON
- **Authentication**: None required
- **Source Name**: "NWS"

### USGS Earthquakes
- **Endpoint**: Public API
- **Data**: Earthquake events
- **Format**: GeoJSON
- **Authentication**: None required
- **Source Name**: "USGS_Earthquakes"

### USGS NWIS
- **Endpoint**: Public API
- **Data**: River gauge readings
- **Format**: JSON
- **Authentication**: None required
- **Source Name**: "USGS_NWIS"

### NASA FIRMS
- **Endpoint**: API (requires key)
- **Data**: Fire/thermal anomalies
- **Format**: CSV (converted to JSON)
- **Authentication**: API key
- **Source Name**: "NASA_FIRMS"
- **Behavior**: Skips gracefully if key missing

### WMATA
- **Endpoint**: API (requires key)
- **Data**: Transit incidents
- **Format**: JSON
- **Authentication**: API key
- **Source Name**: "WMATA"
- **Behavior**: Skips gracefully if key missing

## File Structure

```
ai-based-emergency-alert-sytem/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # SQLAlchemy models (3 tables)
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── database.py          # DB connection
│   │   ├── settings.py          # Configuration
│   │   ├── routers/
│   │   │   └── alerts.py        # API routes
│   │   ├── services/
│   │   │   ├── ingest_base.py   # Base class
│   │   │   ├── ingest_nws.py
│   │   │   ├── ingest_usgs_eq.py
│   │   │   ├── ingest_nwis.py
│   │   │   ├── ingest_fires.py
│   │   │   ├── ingest_wmata.py
│   │   │   ├── ingest_scheduler.py
│   │   │   └── classify.py      # Classification
│   │   └── utils/
│   │       ├── dedupe.py        # Natural keys
│   │       ├── time_utils.py    # Time handling
│   │       ├── geo_utils.py     # Coordinate extraction
│   │       └── backfill_coordinates.py
│   ├── alembic/                 # Migrations
│   ├── requirements.txt         # Dependencies
│   └── .env                     # Configuration
├── frontend/
│   ├── index.html               # Dashboard (with filters)
│   └── map.html                 # Map view
├── docker-compose.yml           # PostgreSQL
├── start-backend.ps1            # Helper scripts
├── start-ingestion.ps1
├── start-classifier.ps1
└── README.md                    # Documentation
```

## Development Constraints

### Python Version
- Minimum: Python 3.10
- Recommended: Python 3.12
- No async/await support in older versions

### Database
- PostgreSQL 16 recommended
- Could work with PostgreSQL 14+
- SQLite possible but not recommended for production

### Operating System
- Windows (PowerShell scripts provided)
- Linux (standard commands)
- macOS (standard commands)

### Ports Used
- **8000**: FastAPI backend
- **3000**: Frontend server (optional)
- **5432**: PostgreSQL
- **11434**: Ollama (optional)

## Testing

### Manual Testing
- Health check: `http://localhost:8000/api/health`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000` or open `index.html`
- Map view: `http://localhost:3000/map.html`

### Database Verification
```sql
SELECT COUNT(*) FROM alerts;
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
SELECT * FROM classifications;
SELECT source, COUNT(*) FROM alerts GROUP BY source;
```

## Troubleshooting

### Database Connection Failed
- Check Docker: `docker-compose ps`
- Verify credentials in `.env`
- Wait 10 seconds after starting container

### Port Already in Use
- Windows: `Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process`
- Change ports in configuration

### CORS Errors
- Use HTTP server for frontend (not file://)
- Check CORS_ORIGINS in `.env`

### No Alerts Appearing
- Run ingestion scheduler: `./start-ingestion.ps1`
- Check TEST_MODE setting
- Verify database has data: `SELECT COUNT(*) FROM alerts;`

### Ollama Connection Issues
- Verify Ollama is running: `curl http://localhost:11434/api/version`
- Check `OLLAMA_BASE_URL` in `.env`
- System falls back to rule-based classification automatically

### TEST_MODE Changes Not Reflecting
- Restart backend API server
- Restart ingestion scheduler
- Classification worker doesn't need restart

## Production Considerations

### Deployment Targets
- **Backend**: Railway, Render, AWS EC2, DigitalOcean
- **Database**: AWS RDS, Supabase, Railway DB
- **Frontend**: Vercel, Netlify, Cloudflare Pages
- **LLM**: Self-hosted Ollama or cloud API (OpenAI, Anthropic)

### Security Checklist
- ✅ Environment variables (never commit `.env`)
- ✅ Strong database passwords
- ✅ HTTPS only in production
- ✅ CORS whitelist specific origins
- ⚠️ Rate limiting (future)
- ⚠️ User authentication (future)
- ⚠️ Regular security updates

### Performance Tuning
- Database connection pooling (SQLAlchemy default)
- Indexes on frequently queried columns
- Pagination to limit response size
- Client-side filtering for instant response
- Consider caching for frequently accessed data
