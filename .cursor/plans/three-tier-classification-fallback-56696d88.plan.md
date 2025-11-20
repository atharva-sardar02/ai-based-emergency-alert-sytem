<!-- 56696d88-cb33-465e-a92f-a5b1e48febf7 2ba42ca6-27d5-4449-909b-5d7f81c69da8 -->
# Unified Backend Startup Implementation

## Overview

Combine the three separate backend processes into a single FastAPI application:

- **API Server** (FastAPI) - serves HTTP requests
- **Ingestion Scheduler** - runs APScheduler for periodic data fetching
- **Classification Worker** - continuously classifies unclassified alerts

All three will run as background tasks within the FastAPI application lifecycle.

## Implementation Steps

### 1. Modify `backend/app/main.py`

#### Add Background Task Management

- Import necessary modules: `asyncio`, ingestion scheduler, classification worker
- Create background task variables to store scheduler and worker references
- Use FastAPI's `@app.on_event("startup")` to start background tasks
- Use `@app.on_event("shutdown")` to gracefully stop background tasks

#### Start Ingestion Scheduler as Background Task

- Import `start_scheduler` from `app.services.ingest_scheduler`
- Create async task that:
  - Runs initial ingestion immediately
  - Starts APScheduler
  - Keeps scheduler running in background
- Store scheduler reference for shutdown

#### Start Classification Worker as Background Task

- Import `classification_worker` from `app.services.classify`
- Use `asyncio.create_task()` to run classification worker in background
- Store task reference for cancellation on shutdown

#### Graceful Shutdown

- On shutdown event:
  - Stop APScheduler gracefully
  - Cancel classification worker task
  - Wait for tasks to complete (with timeout)

### 2. Refactor Service Modules (if needed)

#### Check `ingest_scheduler.py`

- Ensure `start_scheduler()` returns scheduler that can be stopped
- Verify scheduler can run in background without blocking

#### Check `classify.py`

- Ensure `classification_worker()` can run as background task
- Verify it handles cancellation gracefully

### 3. Optional: Serve Frontend from FastAPI

#### Add Static File Serving

- Use FastAPI's `StaticFiles` to serve `frontend/` directory
- Mount at root or `/dashboard` path
- This eliminates need for separate frontend server

### 4. Update Startup Scripts

#### Modify `start-backend.ps1`

- Update comments to indicate it now starts all services
- Keep script simple (just starts FastAPI)

#### Update Documentation

- `HOW_TO_RUN_LOCALLY.md` - reduce from 4 terminals to 1-2
- Update memory bank files to reflect new architecture
- Note that services can still be run separately for debugging

### 5. Add Configuration Option (Optional)

#### Add Setting for Unified Mode

- Add `UNIFIED_MODE: bool = True` to settings
- If `False`, don't start background tasks (for debugging)
- Allows running services separately when needed

## Files to Modify

1. `backend/app/main.py` - Add background task startup/shutdown
2. `start-backend.ps1` - Update comments
3. `HOW_TO_RUN_LOCALLY.md` - Simplify startup instructions
4. `backend/app/settings.py` - Optional: Add UNIFIED_MODE setting

## Files to Review (No Changes Expected)

1. `backend/app/services/ingest_scheduler.py` - Verify scheduler can run in background
2. `backend/app/services/classify.py` - Verify worker can run as background task

## Implementation Details

### Background Task Pattern

```python
@app.on_event("startup")
async def startup_event():
    # Start ingestion scheduler
    scheduler = start_scheduler()
    app.state.scheduler = scheduler
    
    # Start classification worker
    classification_task = asyncio.create_task(classification_worker())
    app.state.classification_task = classification_task

@app.on_event("shutdown")
async def shutdown_event():
    # Stop scheduler
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown()
    
    # Cancel classification worker
    if hasattr(app.state, 'classification_task'):
        app.state.classification_task.cancel()
        try:
            await app.state.classification_task
        except asyncio.CancelledError:
            pass
```

### Frontend Serving (Optional)

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
```

## Benefits

- **Simplified Development**: One command instead of three
- **Easier Deployment**: Single process to manage
- **Better Resource Management**: Shared database connections
- **Consistent Logging**: All services log to same process
- **Graceful Shutdown**: Coordinated shutdown of all services

## Backward Compatibility

- Keep existing service modules unchanged (can still run separately)
- Keep existing startup scripts (for debugging/testing)
- Add configuration option to disable unified mode if needed

## Testing Considerations

- Verify all three services start correctly
- Verify ingestion runs on schedule
- Verify classification worker processes alerts
- Verify graceful shutdown works
- Test with unified mode enabled/disabled
- Verify frontend serving (if implemented)

## Migration Path

1. Implement unified startup in `main.py`
2. Test thoroughly
3. Update documentation
4. Keep old scripts for reference/debugging
5. Users can gradually migrate to unified mode

### To-dos

- [ ] Modify main.py to start ingestion scheduler and classification worker as background tasks on startup
- [ ] Add shutdown event handlers to gracefully stop scheduler and cancel classification worker
- [ ] Verify ingestion scheduler can run as background task without blocking
- [ ] Verify classification worker can run as background task
- [ ] Optionally add static file serving for frontend from FastAPI
- [ ] Update start-backend.ps1 comments to reflect unified mode
- [ ] Update HOW_TO_RUN_LOCALLY.md and memory bank to reflect simplified startup