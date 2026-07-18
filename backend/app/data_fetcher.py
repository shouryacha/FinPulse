"""Thin wrapper around yfinance: pulls fundamentals + OHLCV and upserts them into the DB.

Kept deliberately simple (loop over tickers, catch-and-log per ticker) rather than
batching, since 20 tickers refreshed every ~15 minutes doesn't need to be fast --
it needs to not take the whole refresh down when one ticker's data is temporarily
unavailable from Yahoo Finance.
"""

import logging
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.config import COMPANIES, HISTORY_PERIOD, TICKERS
from app.models import Company, PriceHistory, StockSnapshot

logger = logging.getLogger("finpulse.data_fetcher")


def ensure_companies(db: Session) -> None:
    """Make sure every configured ticker has a Company row (id/name/sector)."""
    existing = {c.ticker for c in db.query(Company.ticker).all()}
    for ticker, (name, sector) in COMPANIES.items():
        if ticker not in existing:
            db.add(Company(ticker=ticker, name=name, sector=sector))
    db.commit()


def _fetch_snapshot(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        fast = t.fast_info
        # yfinance's FastInfo only honors camelCase in .get(), but exposes
        # snake_case via attribute access -- use getattr to get real values.
        price = getattr(fast, "last_price", None)
        prev_close = getattr(fast, "previous_close", None)
        if price is None:
            return None

        day_change_pct = 0.0
        if prev_close:
            day_change_pct = ((price - prev_close) / prev_close) * 100

        pe_ratio = None
        eps = None
        try:
            info = t.info
            pe_ratio = info.get("trailingPE")
            eps = info.get("trailingEps")
        except Exception:
            logger.warning("Could not fetch .info for %s (PE/EPS will be null)", ticker)

        return {
            "price": price,
            "day_change_pct": day_change_pct,
            "market_cap": getattr(fast, "market_cap", None),
            "pe_ratio": pe_ratio,
            "eps": eps,
            "volume": getattr(fast, "last_volume", None),
        }
    except Exception:
        logger.exception("Failed to fetch snapshot for %s", ticker)
        return None


def _upsert_snapshot(db: Session, ticker: str, data: dict) -> None:
    snapshot = db.get(StockSnapshot, ticker)
    if snapshot is None:
        snapshot = StockSnapshot(ticker=ticker)
        db.add(snapshot)

    snapshot.price = data["price"]
    snapshot.day_change_pct = data["day_change_pct"]
    snapshot.market_cap = data["market_cap"]
    snapshot.pe_ratio = data["pe_ratio"]
    snapshot.eps = data["eps"]
    snapshot.volume = data["volume"]
    snapshot.updated_at = datetime.now(timezone.utc)


def _backfill_history(db: Session, ticker: str) -> None:
    """Populate price_history for a ticker if it has no rows yet."""
    has_history = db.query(PriceHistory.id).filter_by(ticker=ticker).first()
    if has_history:
        return

    try:
        hist = yf.Ticker(ticker).history(period=HISTORY_PERIOD)
    except Exception:
        logger.exception("Failed to backfill history for %s", ticker)
        return

    if hist.empty:
        return

    rows = [
        PriceHistory(
            ticker=ticker,
            trade_date=idx.date(),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=float(row["Volume"]) if pd.notna(row["Volume"]) else None,
        )
        for idx, row in hist.iterrows()
    ]
    db.bulk_save_objects(rows)


def refresh_all(db: Session) -> dict:
    """Refresh snapshot + (first-time) history for every tracked ticker."""
    ensure_companies(db)

    succeeded, failed = [], []
    for ticker in TICKERS:
        data = _fetch_snapshot(ticker)
        if data is None:
            failed.append(ticker)
            continue
        _upsert_snapshot(db, ticker, data)
        _backfill_history(db, ticker)
        succeeded.append(ticker)
        db.commit()

    return {"succeeded": succeeded, "failed": failed}
