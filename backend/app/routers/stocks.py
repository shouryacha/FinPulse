from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, PriceHistory, StockSnapshot
from app.schemas import PriceBarOut, StockOut

router = APIRouter(tags=["stocks"])


def _to_stock_out(company: Company, snapshot: StockSnapshot | None) -> StockOut:
    return StockOut(
        ticker=company.ticker,
        name=company.name,
        sector=company.sector,
        price=snapshot.price if snapshot else None,
        day_change_pct=snapshot.day_change_pct if snapshot else None,
        market_cap=snapshot.market_cap if snapshot else None,
        pe_ratio=snapshot.pe_ratio if snapshot else None,
        eps=snapshot.eps if snapshot else None,
        volume=snapshot.volume if snapshot else None,
        updated_at=snapshot.updated_at if snapshot else None,
    )


@router.get("/stocks", response_model=list[StockOut])
def list_stocks(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.ticker).all()
    return [_to_stock_out(c, c.snapshot) for c in companies]


@router.get("/stocks/{ticker}", response_model=StockOut)
def get_stock(ticker: str, db: Session = Depends(get_db)):
    company = db.get(Company, ticker.upper())
    if company is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker '{ticker}'")
    return _to_stock_out(company, company.snapshot)


@router.get("/stocks/{ticker}/history", response_model=list[PriceBarOut])
def get_stock_history(
    ticker: str,
    days: int = Query(365, ge=1, le=3650, description="Number of most recent trading days to return"),
    db: Session = Depends(get_db),
):
    company = db.get(Company, ticker.upper())
    if company is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker '{ticker}'")

    bars = (
        db.query(PriceHistory)
        .filter(PriceHistory.ticker == ticker.upper())
        .order_by(PriceHistory.trade_date.desc())
        .limit(days)
        .all()
    )
    return list(reversed(bars))
