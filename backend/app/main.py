"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
import logging
import os

from app.settings import settings
from app.database import engine, get_db
from app import models
from app.routers import alerts
from app.schemas import HealthCheckResponse

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

# Include routers
app.include_router(alerts.router, prefix="/api", tags=["alerts"])


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting Alexandria Emergency Alert System")
    logger.info(f"Test Mode: {settings.TEST_MODE}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")


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
    """Root endpoint - serve the dashboard if available."""
    dashboard_path = "../alexandria-dashboard-current.html"
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {
        "message": "Alexandria Emergency Alert System API",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

