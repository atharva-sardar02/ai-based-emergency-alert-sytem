# System Patterns: Architecture & Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Dashboard)                      │
│  • Vanilla HTML/CSS/JavaScript                              │
│  • Source filter bar (dynamic checkboxes)                   │
│  • Auto-refresh every 60 seconds                            │
│  • REST API communication                                   │
│  • Interactive map with Leaflet.js                          │
└──────────────────┬──────────────────────────────────────────┘
                   │ REST API (HTTP)
┌──────────────────▼──────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  • FastAPI application (port 8000)                          │
│  • SQLAlchemy ORM                                            │
│  • RESTful endpoints with pagination                         │
│  • Source filtering support                                  │
└─────┬─────────────────────┬─────────────────────┬──────────┘
      │                     │                     │
┌─────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  INGESTION   │  │ CLASSIFICATION  │  │   DEDUPLICATION │
│   SERVICE    │  │     SERVICE     │  │     SERVICE     │
│              │  │                 │  │                 │
│ • Scheduler  │  │ • LLM (Ollama) │  │ • Natural keys  │
│ • 5min cycle │  │ • Rule fallback│  │ • Unique index  │
│ • All 5 srcs │  │ • OLLAMA_BASE_ │  │ • SHA256 hash   │
│              │  │   URL explicit │  │                 │
└─────┬────────┘  └────────┬────────┘  └────────┬────────┘
      │                    │                     │
      └────────────────────┼─────────────────────┘
                           │
                  ┌────────▼────────┐
                  │   PostgreSQL    │
                  │    Database     │
                  │                 │
                  │ • alerts (17 cols)│
                  │ • classifications (6 cols)│
                  │ • user_actions (6 cols)│
                  └─────────────────┘
```

## Core Design Patterns

### 1. Base Class Pattern for Ingestion

**Pattern**: Abstract base class with template method
**Location**: `app/services/ingest_base.py`

All ingestion services inherit from `BaseIngestionService`:
- Abstract methods: `fetch_raw_data()`, `normalize_item()`, `extract_items()`
- Concrete method: `run()` orchestrates the flow
- Common logic: natural key generation, deduplication, database insertion

**Benefits**:
- Consistent ingestion flow across all sources
- Easy to add new sources (just implement abstract methods)
- Centralized error handling and logging
- DRY principle applied

**Example Usage**:
```python
class IngestNWS(BaseIngestionService):
    async def fetch_raw_data(self):
        # Fetch from NWS API
        pass
    
    def extract_items(self, raw_data):
        # Extract items from response
        pass
    
    def normalize_item(self, raw_item):
        # Convert NWS format to common schema
        pass
```

### 2. Natural Key Deduplication

**Pattern**: Deterministic hash-based uniqueness
**Location**: `app/utils/dedupe.py`

Natural key format: `SHA256(source + provider_id + effective_timestamp)`
- Database unique constraint on `natural_key` column
- Prevents duplicates even across retries
- Handles timezone and clock skew issues
- Falls back to content-based key if provider_id missing

**Benefits**:
- Database-level enforcement (cannot have duplicates)
- Works even if ingestion runs multiple times
- Handles sources without reliable IDs

### 3. Classification Strategy Pattern

**Pattern**: LLM with rule-based fallback
**Location**: `app/services/classify.py`

Two classification strategies:
1. **Primary**: LLM via Ollama (if available, uses explicit OLLAMA_BASE_URL)
2. **Fallback**: Rule-based mapping (severity + urgency → criticality)

**Workflow**:
1. Check if LLM available (Ollama client with explicit host)
2. Try LLM classification
3. If unavailable or error, use rule-based
4. Store result with model_version indicating method used

**Benefits**:
- System works even without LLM
- Transparent about classification method
- Easy to add more strategies
- Explicit connection configuration

### 4. Repository Pattern (Implicit)

**Pattern**: SQLAlchemy ORM as data access layer
**Location**: `app/models.py`, `app/database.py`

Database operations abstracted through SQLAlchemy:
- Models define schema (3 tables, 29 total columns)
- Session management via dependency injection
- Relationships handled by ORM
- Indexes for performance

**Benefits**:
- Clean separation of data access
- Easy to test with in-memory database
- Migration support via Alembic

### 5. Dependency Injection (FastAPI)

**Pattern**: FastAPI's dependency injection for database sessions
**Location**: `app/database.py`, `app/routers/alerts.py`

FastAPI provides database sessions to route handlers:
- `get_db()` dependency creates/manages sessions
- Automatic cleanup on request completion
- Easy to override for testing

**Example**:
```python
@router.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    # db session automatically provided
    pass
```

### 6. Client-Side Filtering Pattern

**Pattern**: Dynamic filter generation with client-side filtering
**Location**: `frontend/index.html`

**Implementation**:
- Filter options generated dynamically from active sources
- Client-side filtering for instant response
- Filter state cached in memory
- No server round-trips for filtering

**Benefits**:
- Instant filtering response
- Reduced server load
- Better user experience
- Works offline (after initial load)

## Component Relationships

### Ingestion Flow
```
Scheduler → BaseIngestionService.run()
    ↓
fetch_raw_data() → Raw Data
    ↓
extract_items() → List[Raw Items]
    ↓
normalize_item() → Normalized Alert
    ↓
generate_natural_key() → SHA256 hash
    ↓
DB Insert (ignore duplicates) → Alert stored
    ↓
Extract coordinates (if available) → lat/lon stored
    ↓
Trigger Classification (async)
```

### API Request Flow
```
Frontend Request → FastAPI Router
    ↓
get_db() → Database Session
    ↓
SQLAlchemy Query → Database
    ↓
Pydantic Schema → JSON Response
    ↓
Frontend Renders + Filters
```

### Classification Flow
```
Unclassified Alert → Classify Service
    ↓
Check Ollama Availability (explicit OLLAMA_BASE_URL)
    ↓
[If Available] → LLM Classification → Store Result
[If Unavailable] → Rule-Based Classification → Store Result
```

### Filtering Flow
```
Alerts Loaded → Extract Unique Sources
    ↓
Generate Filter Checkboxes → User Interface
    ↓
User Selects Filters → Client-Side Filter
    ↓
Update Display → Show Filtered Alerts
```

## Data Model Relationships

```
Alert (1) ──→ (many) Classification
  │
  └──→ (many) UserAction
```

- One alert can have multiple classifications (for model versioning)
- One alert can have multiple user actions (for audit trail)
- Cascade delete ensures referential integrity
- Geographic coordinates stored directly on Alert for map visualization

## Key Technical Decisions

### 1. PostgreSQL over SQLite
- **Reason**: Multi-user support, production-ready, better concurrent access
- **Trade-off**: Requires Docker Compose setup
- **Benefit**: Proper foreign keys, better performance, spatial queries ready

### 2. FastAPI over Flask
- **Reason**: Better async support, automatic OpenAPI docs, type hints
- **Trade-off**: Learning curve (minimal)
- **Benefit**: Modern Python patterns, excellent performance

### 3. Vanilla JavaScript Frontend
- **Reason**: MVP simplicity, no build step needed
- **Trade-off**: No React/component structure
- **Benefit**: Fast iteration, easy to understand, client-side filtering

### 4. Ollama for LLM
- **Reason**: Local execution, free, offline capability
- **Trade-off**: Requires model download
- **Benefit**: No API costs, privacy, fast inference
- **Enhancement**: Explicit OLLAMA_BASE_URL configuration

### 5. APScheduler for Scheduling
- **Reason**: Simple, Python-native, async support
- **Trade-off**: Single-process scheduling
- **Benefit**: Easy setup, sufficient for MVP scale

### 6. Client-Side Filtering
- **Reason**: Instant response, reduced server load
- **Trade-off**: All data loaded initially
- **Benefit**: Better UX, works with pagination

## Error Handling Strategy

1. **Ingestion Errors**: Log and continue with next source
2. **Database Errors**: Log, prevent duplicate via constraint
3. **LLM Errors**: Fallback to rule-based classification
4. **API Errors**: Return appropriate HTTP status codes
5. **Network Errors**: Retry with backoff in scheduler
6. **Missing API Keys**: Gracefully skip optional sources

## Extension Points

### Adding New Data Source
1. Create `ingest_newsource.py` in `app/services/`
2. Inherit from `BaseIngestionService`
3. Implement `fetch_raw_data()`, `extract_items()`, and `normalize_item()`
4. Add to scheduler in `ingest_scheduler.py`
5. Filter options automatically appear in frontend

### Adding New Classification Strategy
1. Add new method in `classify.py`
2. Update fallback logic
3. Update model_version naming

### Adding New API Endpoint
1. Add route in `app/routers/alerts.py`
2. Define Pydantic schema in `app/schemas.py`
3. Add database query logic
4. Document in OpenAPI (automatic)

### Adding New Filter Type
1. Add filter UI element in `frontend/index.html`
2. Update `renderAlerts()` to apply filter
3. Update `updateFilterOptions()` if needed

## Performance Considerations

- **Database Indexes**: On `effective_at`, `source`, `provider_id`, `criticality`, `latitude`, `longitude`
- **Pagination**: All list endpoints support page/limit
- **Async Operations**: Ingestion and classification are async
- **Connection Pooling**: SQLAlchemy handles connection management
- **Client-Side Filtering**: No server load for filtering
- **Parallel Ingestion**: All sources fetched in parallel

## Security Patterns

- **Environment Variables**: All secrets in `.env` (not committed, .gitignore protected)
- **CORS Configuration**: Whitelist specific origins
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **Input Validation**: Pydantic schemas validate all inputs
- **No PII**: System doesn't store personal information in MVP
- **API Key Protection**: Comprehensive .gitignore prevents accidental commits

## Frontend Patterns

### Dynamic Source Display
- Sources list populated from actual alert data
- Only shows sources with alerts
- Updates automatically as new sources appear

### Source Filtering
- Checkboxes generated dynamically
- Client-side filtering for instant response
- Multiple sources can be selected
- Clear button resets all filters

### Irrelevant Alert Handling
- Alerts marked irrelevant move to bottom
- Faded appearance (50% opacity)
- Badge indicates status
- Button removed after marking
- Remains visible for reference
