from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.data_fetcher import refresh_all
from app.database import get_db
from app.models import Company
from app.routers.stocks import _to_stock_out
from app.schemas import MarketSummaryOut

router = APIRouter(tags=["market"])


@router.get("/market-summary", response_model=MarketSummaryOut)
def market_summary(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    snapshots = [(c, c.snapshot) for c in companies if c.snapshot is not None]

    total_market_cap = sum(s.market_cap for _, s in snapshots if s.market_cap)
    pe_values = [s.pe_ratio for _, s in snapshots if s.pe_ratio]
    average_pe = sum(pe_values) / len(pe_values) if pe_values else None

    gainers = [(c, s) for c, s in snapshots if s.day_change_pct > 0]
    losers = [(c, s) for c, s in snapshots if s.day_change_pct < 0]
    unchanged = len(snapshots) - len(gainers) - len(losers)

    top_gainer = max(gainers, key=lambda pair: pair[1].day_change_pct, default=None)
    top_loser = min(losers, key=lambda pair: pair[1].day_change_pct, default=None)

    return MarketSummaryOut(
        tracked_companies=len(companies),
        total_market_cap=total_market_cap,
        average_pe_ratio=average_pe,
        gainers=len(gainers),
        losers=len(losers),
        unchanged=unchanged,
        top_gainer=_to_stock_out(*top_gainer) if top_gainer else None,
        top_loser=_to_stock_out(*top_loser) if top_loser else None,
    )


@router.post("/refresh")
def trigger_refresh(db: Session = Depends(get_db)):
    """Manually trigger a data refresh from yfinance (also runs on a schedule)."""
    return refresh_all(db)
