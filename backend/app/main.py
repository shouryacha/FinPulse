import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data_fetcher import refresh_all
from app.database import Base, SessionLocal, engine
from app.routers import market, stocks
from app.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finpulse.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        result = refresh_all(db)
        logger.info(
            "Initial refresh done: %d succeeded, %d failed",
            len(result["succeeded"]),
            len(result["failed"]),
        )
    except Exception:
        logger.exception("Initial refresh failed; dashboard will show stale/empty data until next cycle")
    finally:
        db.close()

    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="FinPulse API",
    description="REST API for the FinPulse stock market monitoring dashboard.",
    version="1.0.0",
    lifespan=lifespan,
)

# Streamlit Cloud + local dev frontends call this API cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(market.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "FinPulse API"}
