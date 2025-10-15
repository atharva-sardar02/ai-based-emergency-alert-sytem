"""Scheduler for running ingestion jobs periodically."""
import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.settings import settings
from app.services.ingest_nws import IngestNWS
from app.services.ingest_usgs_eq import IngestUSGSEarthquakes
from app.services.ingest_nwis import IngestNWIS
from app.services.ingest_fires import IngestFires
from app.services.ingest_wmata import IngestWMATA

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_nws_ingestion():
    """Run NWS ingestion job."""
    db = SessionLocal()
    try:
        service = IngestNWS(db)
        count = await service.run()
        logger.info(f"NWS ingestion completed: {count} new alerts")
    except Exception as e:
        logger.error(f"NWS ingestion failed: {e}", exc_info=True)
    finally:
        db.close()


async def run_usgs_eq_ingestion():
    """Run USGS Earthquake ingestion job."""
    db = SessionLocal()
    try:
        service = IngestUSGSEarthquakes(db)
        count = await service.run()
        logger.info(f"USGS Earthquake ingestion completed: {count} new alerts")
    except Exception as e:
        logger.error(f"USGS Earthquake ingestion failed: {e}", exc_info=True)
    finally:
        db.close()


async def run_nwis_ingestion():
    """Run USGS NWIS ingestion job."""
    db = SessionLocal()
    try:
        service = IngestNWIS(db)
        count = await service.run()
        logger.info(f"NWIS ingestion completed: {count} new alerts")
    except Exception as e:
        logger.error(f"NWIS ingestion failed: {e}", exc_info=True)
    finally:
        db.close()


async def run_fires_ingestion():
    """Run NASA FIRMS fire detection ingestion job."""
    db = SessionLocal()
    try:
        service = IngestFires(db)
        count = await service.run()
        logger.info(f"FIRMS fire detection ingestion completed: {count} new alerts")
    except Exception as e:
        logger.error(f"FIRMS ingestion failed: {e}", exc_info=True)
    finally:
        db.close()


async def run_wmata_ingestion():
    """Run WMATA transit incident ingestion job."""
    db = SessionLocal()
    try:
        service = IngestWMATA(db)
        count = await service.run()
        logger.info(f"WMATA ingestion completed: {count} new alerts")
    except Exception as e:
        logger.error(f"WMATA ingestion failed: {e}", exc_info=True)
    finally:
        db.close()


async def run_all_ingestions():
    """Run all ingestion jobs in parallel."""
    logger.info("Starting all ingestion jobs...")
    await asyncio.gather(
        run_nws_ingestion(),
        run_usgs_eq_ingestion(),
        run_nwis_ingestion(),
        run_fires_ingestion(),
        run_wmata_ingestion(),
        return_exceptions=True
    )
    logger.info("All ingestion jobs completed")


def start_scheduler():
    """Start the ingestion scheduler."""
    scheduler = AsyncIOScheduler()
    
    # Schedule ingestion jobs
    interval_seconds = settings.REFRESH_INTERVAL_SECONDS
    
    scheduler.add_job(
        run_all_ingestions,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id='ingest_all',
        name='Run all ingestion jobs',
        replace_existing=True
    )
    
    logger.info(f"Scheduler started - ingestion interval: {interval_seconds}s")
    logger.info(f"Test Mode: {settings.TEST_MODE}")
    
    scheduler.start()
    return scheduler


async def main():
    """Main entry point for the scheduler."""
    logger.info("=" * 60)
    logger.info("Alexandria Emergency Alert System - Ingestion Scheduler")
    logger.info("=" * 60)
    
    # Run immediately on startup
    await run_all_ingestions()
    
    # Start scheduler for periodic runs
    scheduler = start_scheduler()
    
    try:
        # Keep the scheduler running
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

