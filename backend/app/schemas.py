from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    name: str
    sector: str
    price: float | None = None
    day_change_pct: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    eps: float | None = None
    volume: float | None = None
    updated_at: datetime | None = None


class PriceBarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class MarketSummaryOut(BaseModel):
    tracked_companies: int
    total_market_cap: float
    average_pe_ratio: float | None
    gainers: int
    losers: int
    unchanged: int
    top_gainer: StockOut | None
    top_loser: StockOut | None
