import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import REFRESH_INTERVAL_MINUTES
from app.data_fetcher import refresh_all
from app.database import SessionLocal

logger = logging.getLogger("finpulse.scheduler")


def _run_refresh_job() -> None:
    db = SessionLocal()
    try:
        result = refresh_all(db)
        logger.info(
            "Scheduled refresh done: %d succeeded, %d failed",
            len(result["succeeded"]),
            len(result["failed"]),
        )
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _run_refresh_job,
        trigger="interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        id="refresh_all_stocks",
        next_run_time=None,  # first run is triggered explicitly at startup, not immediately again here
    )
    scheduler.start()
    return scheduler
