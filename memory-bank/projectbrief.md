# Project Brief: Alexandria Emergency Alert System

## Project Overview

**Project Name:** Alexandria Emergency Alert System (EAS)  
**Owner:** Atharva Sardar  
**Version:** 0.1.0 (MVP Complete)  
**Status:** Production Ready

## Core Mission

Build a real-time emergency alert system for the City of Alexandria that aggregates, normalizes, classifies, and presents emergency alerts from multiple trusted public sources in a unified dashboard interface with intelligent filtering and map visualization.

## Primary Goals

1. **Multi-Source Aggregation**: Integrate data from 5 public emergency data sources (NWS, USGS Earthquakes, USGS NWIS, NASA FIRMS, WMATA)
2. **Intelligent Classification**: Automatically assess alert criticality (High/Medium/Low) using AI-powered classification
3. **Deduplication**: Prevent duplicate alerts using deterministic natural keys
4. **User Actions**: Enable emergency managers to acknowledge alerts, mark irrelevant items, and add notes
5. **Modern Dashboard**: Provide a clean, responsive interface with source filtering and map visualization
6. **Dynamic Source Display**: Show only active data sources with actual alerts

## Target Users

- **Duty Officer / Emergency Manager** (City EOC staff)
- **Field Responder / Supervisor** (Fire/EMS/Police supervisors)
- **Civic Ops Analyst** (Data/ops team triaging signals)

## Key Constraints & Requirements

### Functional Requirements
- Ingestion from 5 sources (NWS, USGS EQ, USGS NWIS, NASA FIRMS, WMATA)
- Normalization to common alert schema
- Database-level deduplication via natural keys
- AI classification using local/open-source LLM (with rule-based fallback)
- RESTful API for frontend consumption
- User actions: acknowledge and mark irrelevant
- Real-time dashboard with auto-refresh
- Source filtering on dashboard
- Dynamic source list (only active sources)
- Map visualization with geographic coordinates
- Geographic coordinate extraction and storage

### Non-Functional Requirements
- Performance: <500ms for alert listing
- Reliability: Retry logic for transient errors
- Observability: Logging for ingestion success/failure
- Local Development: All services runnable locally
- Privacy: No PII in MVP
- Security: Environment variable handling, CORS configuration, .gitignore protection

### Out of Scope (MVP)
- User authentication/authorization
- Real-time websockets (polling acceptable)
- Advanced analytics dashboards
- Automated escalation (email/SMS)
- Mobile app

## Success Criteria

✅ **MVP Complete**: System ingests, deduplicates, classifies, and serves alerts
✅ **Multi-Source**: 5 data sources integrated (3 always work, 2 optional with keys)
✅ **AI Classification**: LLM-powered with intelligent fallback
✅ **User Actions**: Acknowledge and irrelevant marking functional
✅ **Source Filtering**: Filter alerts by data source
✅ **Dynamic Display**: Only active sources shown
✅ **Map Visualization**: Interactive map with alert markers
✅ **Production Ready**: Database migrations, error handling, documentation

## Technical Approach

Selected **Option A: FastAPI + PostgreSQL + Background Tasks**
- Fast API development with excellent typing
- Simple background task execution
- Strong async HTTP client support
- Easy local LLM integration (Ollama)
- SQLAlchemy ORM with Alembic migrations
- Client-side filtering for instant response

## Geographic Scope

**Production Mode** (TEST_MODE=false):
- Alexandria-specific queries and bounding boxes
- 10km radius from Alexandria City Hall for earthquakes
- Alexandria bounding box for FIRMS

**Test Mode** (TEST_MODE=true):
- Virginia-wide alerts for demonstrations
- Global earthquakes M4.5+
- Virginia-wide FIRMS coverage
- Better coverage for demos

## Data Sources

1. **NWS** (National Weather Service) - Weather alerts, watches, advisories (always available)
2. **USGS Earthquakes** - Seismic activity monitoring (always available)
3. **USGS NWIS** - River gauge data for flood monitoring (always available)
4. **NASA FIRMS** - Satellite-based fire detection (requires API key, gracefully skipped if missing)
5. **WMATA** - Metro transit incident alerts (requires API key, gracefully skipped if missing)

## Database Schema

### Tables (3 total, 29 columns)

**alerts** (17 columns):
- Core: id, natural_key (unique), source, provider_id
- Content: title, summary, event_type, severity, urgency, area
- Time: effective_at, expires_at, created_at
- Location: latitude, longitude
- Provenance: url, raw_payload

**classifications** (6 columns):
- id, alert_id (FK), criticality, rationale, model_version, created_at

**user_actions** (6 columns):
- id, alert_id (FK), action, note, actor, created_at

## Project Timeline

- **Milestone 1**: Skeleton (FastAPI + DB schema) ✅
- **Milestone 2**: Multi-source ingestion ✅
- **Milestone 3**: LLM classification ✅
- **Milestone 4**: Frontend integration ✅
- **Milestone 5**: Detail view & user actions ✅
- **Milestone 6**: Polish & documentation ✅
- **Enhancement 1**: Source filtering ✅
- **Enhancement 2**: Dynamic source display ✅
- **Enhancement 3**: Map visualization ✅
- **Enhancement 4**: Geographic coordinates ✅

**Current Status**: MVP Complete and Production Ready

## Recent Enhancements

### Source Filtering (October 2025)
- Filter bar at top of dashboard
- Dynamic checkbox generation from active sources
- Client-side filtering for instant response
- Clear button to reset filters

### Dynamic Source Display
- Sidebar shows only sources with actual alerts
- Updates automatically as new sources appear
- No hardcoded source list

### Button Updates
- "View More" → "Know More"
- "Not Relevant" → "Irrelevant"
- Irrelevant alerts move to bottom (faded) but remain visible

### Map Visualization
- Interactive map with Leaflet.js
- Alert markers with coordinates
- Color-coded by criticality
- Source-specific icons
- Filtering support

### Ollama Connection Fix
- Explicit use of OLLAMA_BASE_URL from settings
- Better error handling and logging
- Graceful fallback to rule-based classification

## Quick Start

**One-time Setup**:
1. `docker-compose up -d`
2. `cd backend && python -m venv venv && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt && alembic upgrade head`

**Every Run** (4 terminals):
1. `./start-backend.ps1`
2. `./start-ingestion.ps1`
3. `./start-classifier.ps1`
4. `cd frontend && python -m http.server 3000`

**Open**: http://localhost:3000
