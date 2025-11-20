"""Main FastAPI application entry point."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
import logging
import os
import asyncio

from app.settings import settings
from app.database import engine, get_db
from app import models
from app.routers import alerts, auth
from app.schemas import HealthCheckResponse
from app.services.ingest_scheduler import start_scheduler, run_all_ingestions
from app.services.classify import classification_worker

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Alexandria Emergency Alert System",
    description="Real-time emergency alert aggregation and classification",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (must be before static file mounting)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])

# Determine frontend path for serving HTML files
# __file__ is backend/app/main.py, so we need to go up 2 levels to get to project root
frontend_path = None
try:
    # Go from backend/app/main.py -> backend/app -> backend -> project_root
    backend_dir = os.path.dirname(os.path.dirname(__file__))  # backend/app -> backend
    project_root = os.path.dirname(backend_dir)  # backend -> project_root
    frontend_path = os.path.join(project_root, "frontend")
    if os.path.exists(frontend_path):
        logger.info(f"Frontend directory found at: {frontend_path}")
    else:
        logger.warning(f"Frontend directory not found at: {frontend_path}")
        frontend_path = None
except Exception as e:
    logger.warning(f"Could not locate frontend directory: {e}")
    frontend_path = None


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("=" * 60)
    logger.info("Starting Alexandria Emergency Alert System")
    logger.info("=" * 60)
    logger.info(f"Test Mode: {settings.TEST_MODE}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")
    
    # Run initial ingestion immediately
    logger.info("Running initial ingestion...")
    try:
        await run_all_ingestions()
    except Exception as e:
        logger.error(f"Initial ingestion failed: {e}", exc_info=True)
    
    # Start ingestion scheduler as background task
    logger.info("Starting ingestion scheduler...")
    scheduler = start_scheduler()
    app.state.scheduler = scheduler
    logger.info("Ingestion scheduler started")
    
    # Start classification worker as background task
    logger.info("Starting classification worker...")
    classification_task = asyncio.create_task(classification_worker())
    app.state.classification_task = classification_task
    logger.info("Classification worker started")
    
    logger.info("All background services started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down background services...")
    
    # Stop ingestion scheduler
    if hasattr(app.state, 'scheduler'):
        try:
            app.state.scheduler.shutdown(wait=True)
            logger.info("Ingestion scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    # Cancel classification worker
    if hasattr(app.state, 'classification_task'):
        try:
            app.state.classification_task.cancel()
            # Wait for task to finish cancellation (with timeout)
            try:
                await asyncio.wait_for(app.state.classification_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Classification worker shutdown timeout")
            except asyncio.CancelledError:
                # Task was cancelled successfully
                logger.info("Classification worker cancelled")
            except Exception as e:
                logger.warning(f"Classification worker raised exception during shutdown: {e}")
            logger.info("Classification worker stopped")
        except Exception as e:
            logger.error(f"Error stopping classification worker: {e}")
    
    logger.info("Shutdown complete")


@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "degraded",
        timestamp=datetime.utcnow(),
        database=db_status,
        version="0.1.0"
    )


@app.get("/")
async def root():
    """Serve the dashboard index page."""
    if frontend_path:
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {
        "message": "Alexandria Emergency Alert System API",
        "docs": "/docs",
        "health": "/api/health",
        "note": "Frontend not found. Run from project root or check frontend directory."
    }


@app.get("/index.html")
async def index_page():
    """Serve the dashboard index page."""
    if frontend_path:
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index page not found")


@app.get("/map.html")
async def map_page():
    """Serve the map view page."""
    if frontend_path:
        map_path = os.path.join(frontend_path, "map.html")
        if os.path.exists(map_path):
            return FileResponse(map_path)
    raise HTTPException(status_code=404, detail="Map page not found")


@app.get("/login.html")
async def login_page():
    """Serve the login page."""
    if frontend_path:
        login_path = os.path.join(frontend_path, "login.html")
        if os.path.exists(login_path):
            return FileResponse(login_path)
    raise HTTPException(status_code=404, detail="Login page not found")


@app.get("/signup.html")
async def signup_page():
    """Serve the sign up page."""
    if frontend_path:
        signup_path = os.path.join(frontend_path, "signup.html")
        if os.path.exists(signup_path):
            return FileResponse(signup_path)
    raise HTTPException(status_code=404, detail="Sign up page not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

