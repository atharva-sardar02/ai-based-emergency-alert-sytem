# Active Context: Current Work Focus

## Current Status

**MVP Status**: ✅ **COMPLETE AND PRODUCTION READY**

The Alexandria Emergency Alert System MVP is fully functional with all core features implemented, tested, and documented. The system is ready for deployment and use.

## Recent Changes (Latest Updates)

### Latest Enhancements (October 2025)
- ✅ **Source Filtering**: Added filter bar at top of dashboard to filter alerts by data source
- ✅ **Dynamic Source Display**: Dashboard sidebar now shows only active sources (sources with actual alerts)
- ✅ **Updated Button Labels**: Changed "View More" → "Know More", "Not Relevant" → "Irrelevant"
- ✅ **Irrelevant Alert Behavior**: Alerts marked irrelevant move to bottom (faded) but remain visible
- ✅ **Simplified Startup**: Created helper scripts (`start-backend.ps1`, `start-ingestion.ps1`, `start-classifier.ps1`)
- ✅ **Enhanced .gitignore**: Comprehensive protection for API keys and environment files
- ✅ **Ollama Connection Fix**: Updated classifier to explicitly use `OLLAMA_BASE_URL` from settings
- ✅ **Geographic Coordinates**: Added latitude/longitude fields to alerts table for map visualization
- ✅ **Map View**: Interactive map page (`map.html`) with Leaflet.js integration

### Completed Implementation
- ✅ FastAPI backend with PostgreSQL database
- ✅ Multi-source ingestion (NWS, USGS EQ, USGS NWIS, NASA FIRMS, WMATA)
- ✅ Deduplication via natural keys
- ✅ AI classification with Ollama (rule-based fallback)
- ✅ RESTful API with pagination and filtering
- ✅ Beautiful dashboard frontend with source filters
- ✅ Interactive map visualization with Leaflet.js
- ✅ Geographic coordinate extraction and storage
- ✅ User actions (acknowledge, mark irrelevant)
- ✅ Database migrations with Alembic
- ✅ Comprehensive documentation

## Current Work Focus

**No active development tasks** - System is complete and production-ready.

## Weekly Time Tracking Process

**Location**: `toggl/` directory

**Weekly Workflow**:
1. Create breakdown document: `toggl/Week_Nov_DD-DD_YYYY.md` (e.g., `Week_Nov_08-09_2025.md`)
   - Document all weekend work (Saturday & Sunday)
   - Break down by day, session, and task
   - Include troubleshooting time and issues faced
   - Total should be ~20 hours (10 hours per day)

2. Create CSV import file: `toggl/toggl_import_Nov_DD-DD_YYYY.csv`
   - Use template: `toggl/toggl_template.csv`
   - **Critical Format Requirements**:
     - Start date: `YYYY-MM-DD` (e.g., `2025-11-08`)
     - Start time: `HH:MM:SS` (e.g., `09:00:00`) - NOT `HH:MM`
     - Duration: `HH:MM:SS` (e.g., `00:30:00`) - NOT decimal hours
     - Project: "Crowdlabs"
     - Email: "atharva.sardar02@gmail.com"
   - Ensure dates are Saturday and Sunday (not Sunday/Monday)
   - No empty lines at end of file
   - UTF-8 encoding

3. Import to Toggl Track:
   - Settings → Import → Upload CSV
   - Verify preview shows correct entries
   - Import

**Reference**: See `toggl/WEEKLY_TOGGL_TEMPLATE.md` for complete format requirements and examples.

### Immediate Considerations
1. **Configuration**: Set `TEST_MODE=false` in `.env` for production (Alexandria-only alerts)
2. **API Keys**: Optional setup for FIRMS and WMATA sources (see `API_KEYS_INFO.md`)
3. **Ollama Setup**: Optional LLM classification setup (system works with rule-based fallback)
4. **Testing**: Manual testing with real-world data in production mode

### Next Phase (Future Enhancements)
1. User authentication and roles
2. Email/SMS notifications
3. Mobile responsive improvements
4. Advanced analytics
5. Alert clustering on map
6. WebSocket support for real-time updates

## Active Decisions & Considerations

### Configuration
- **TEST_MODE**: 
  - `true` = Virginia-wide alerts (good for demonstrations)
  - `false` = Alexandria-only (production mode)
  - **Note**: When changing TEST_MODE, restart backend API and ingestion scheduler
- **Database**: PostgreSQL via Docker Compose (port 5432)
- **API Keys**: Optional but recommended for complete data coverage

### Service Architecture
- **API Server**: FastAPI on port 8000 (`start-backend.ps1`)
- **Ingestion Scheduler**: Runs all 5 sources every 5 minutes (`start-ingestion.ps1`)
- **Classification Worker**: Continuous polling for unclassified alerts (`start-classifier.ps1`)
- **Frontend**: Served on port 3000 or open `index.html` directly

### Classification Strategy
- **Primary**: Ollama LLM (llama3.2:3b-instruct-q4) via `OLLAMA_BASE_URL`
- **Fallback**: Rule-based classification (severity/urgency mapping)
- Both methods produce High/Medium/Low with rationale
- **Note**: Fixed to explicitly use `OLLAMA_BASE_URL` from settings

### Data Source Priorities
1. **Always Available**: NWS, USGS EQ, USGS NWIS (no API keys needed)
2. **Optional**: NASA FIRMS, WMATA (require free API keys, gracefully skipped if missing)

## Next Steps

### For End Users (Quick Start)
1. **One-time Setup**:
   - Create `backend/.env` file (see `.env.example`)
   - Start PostgreSQL: `docker-compose up -d`
   - Run migrations: `cd backend && alembic upgrade head`

2. **Start Services** (4 terminals):
   ```powershell
   # Terminal 1: Backend API
   ./start-backend.ps1
   
   # Terminal 2: Ingestion (all sources, continuous)
   ./start-ingestion.ps1
   
   # Terminal 3: Classification
   ./start-classifier.ps1
   
   # Terminal 4: Frontend
   cd frontend; python -m http.server 3000
   ```

3. **Open Dashboard**: http://localhost:3000

### For Developers
- Review code structure in `backend/app/`
- All services follow base class pattern (`BaseIngestionService`)
- Easy to add new sources by extending base class
- Database models in `app/models.py` (3 tables: alerts, classifications, user_actions)
- API endpoints in `app/routers/alerts.py`
- Frontend filtering logic in `frontend/index.html`

## Known Issues & Notes

- ✅ System works without API keys (FIRMS and WMATA optional)
- ✅ LLM classification optional (fallback works fine)
- ✅ TEST_MODE provides better demo data (Virginia-wide)
- ✅ Frontend should be served via HTTP (not file://) to avoid CORS issues
- ✅ When changing TEST_MODE, restart backend and ingestion services
- ✅ Ollama connection now explicitly uses `OLLAMA_BASE_URL` from settings

## Current Configuration State

- **Database**: PostgreSQL 16 via Docker Compose
- **Python Version**: 3.12
- **Framework**: FastAPI 0.109
- **Frontend**: Vanilla HTML/CSS/JavaScript with source filtering
- **Classification**: Ollama (llama3.2:3b-instruct-q4) with rule-based fallback
- **Scheduling**: APScheduler (5-minute intervals)
- **Map Library**: Leaflet.js for interactive map visualization

## Database Schema

### Tables (3 total)

1. **alerts** (17 columns)
   - Core: id, natural_key (unique), source, provider_id
   - Content: title, summary, event_type, severity, urgency, area
   - Time: effective_at, expires_at, created_at
   - Location: latitude, longitude (for map)
   - Provenance: url, raw_payload

2. **classifications** (6 columns)
   - id, alert_id (FK), criticality, rationale, model_version, created_at

3. **user_actions** (6 columns)
   - id, alert_id (FK), action, note, actor, created_at

### Indexes
- `alerts.natural_key` (unique)
- `alerts.effective_at`
- `alerts.source`, `alerts.provider_id`
- `alerts.latitude`, `alerts.longitude`
- `classifications.alert_id`, `classifications.criticality`
- `user_actions.alert_id`, `user_actions.action`

## Documentation Status

✅ All documentation complete:
- `README.md` - Comprehensive guide
- `HOW_TO_RUN_LOCALLY.md` - Minimal startup guide (updated with scripts)
- `SETUP_INSTRUCTIONS.md` - Step-by-step setup
- `API_KEYS_INFO.md` - API key instructions
- `COMPLETED_SYSTEM_SUMMARY.md` - Overview
- `CHANGES_MADE.md` - Recent changes summary
- `TEST_NEW_SOURCES.md` - FIRMS/WMATA integration guide

## Dashboard Features (Current)

### Main View
- ✅ Source filter bar at top (dynamically populated)
- ✅ Alerts sorted by relevance (relevant first, irrelevant at bottom)
- ✅ Color-coded criticality badges (High/Medium/Low)
- ✅ "Know More" button opens detail modal
- ✅ "Irrelevant" button moves alert to bottom (faded)
- ✅ Auto-refresh every 60 seconds
- ✅ Dynamic source list in sidebar (only active sources shown)

### Map View
- ✅ Interactive map with Leaflet.js
- ✅ Alert markers with coordinates
- ✅ Color-coded by criticality
- ✅ Source-specific icons
- ✅ Filtering by source and criticality
- ✅ Auto-fit bounds to show all alerts

### Detail Modal
- ✅ Full alert information
- ✅ AI classification rationale
- ✅ Source link
- ✅ Acknowledge form with notes
- ✅ Raw payload display
