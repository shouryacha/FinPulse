from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sector: Mapped[str] = mapped_column(String, nullable=False)

    snapshot: Mapped["StockSnapshot"] = relationship(
        back_populates="company", uselist=False, cascade="all, delete-orphan"
    )
    history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class StockSnapshot(Base):
    """Latest known state for a ticker. One row per company, upserted on refresh."""

    __tablename__ = "stock_snapshot"

    ticker: Mapped[str] = mapped_column(ForeignKey("companies.ticker"), primary_key=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    day_change_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    market_cap: Mapped[float] = mapped_column(Float, nullable=True)
    pe_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    eps: Mapped[float] = mapped_column(Float, nullable=True)
    volume: Mapped[float] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="snapshot")


class PriceHistory(Base):
    """Daily OHLCV bar for a ticker, used to draw historical charts."""

    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("ticker", "trade_date", name="uq_ticker_trade_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("companies.ticker"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="history")
