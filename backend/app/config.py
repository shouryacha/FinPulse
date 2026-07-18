import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./finpulse_dev.db")

# Refresh the snapshot cache this often (minutes) via the background scheduler.
REFRESH_INTERVAL_MINUTES = int(os.environ.get("REFRESH_INTERVAL_MINUTES", "15"))

# How many years of daily history to backfill per ticker on first fetch.
HISTORY_PERIOD = "1y"

# The 20 tracked companies: yfinance ticker -> (display name, sector).
COMPANIES: dict[str, tuple[str, str]] = {
    "RELIANCE.NS": ("Reliance Industries", "Energy"),
    "TCS.NS": ("Tata Consultancy Services", "IT"),
    "INFY.NS": ("Infosys", "IT"),
    "WIPRO.NS": ("Wipro", "IT"),
    "HDFCBANK.NS": ("HDFC Bank", "Financials"),
    "ICICIBANK.NS": ("ICICI Bank", "Financials"),
    "SBIN.NS": ("State Bank of India", "Financials"),
    "KOTAKBANK.NS": ("Kotak Mahindra Bank", "Financials"),
    "AXISBANK.NS": ("Axis Bank", "Financials"),
    "BAJFINANCE.NS": ("Bajaj Finance", "Financials"),
    "ITC.NS": ("ITC Limited", "Consumer Staples"),
    "HINDUNILVR.NS": ("Hindustan Unilever", "Consumer Staples"),
    "NESTLEIND.NS": ("Nestle India", "Consumer Staples"),
    "BHARTIARTL.NS": ("Bharti Airtel", "Telecom"),
    "LT.NS": ("Larsen & Toubro", "Industrials"),
    "MARUTI.NS": ("Maruti Suzuki", "Auto"),
    "ASIANPAINT.NS": ("Asian Paints", "Consumer Discretionary"),
    "TITAN.NS": ("Titan Company", "Consumer Discretionary"),
    "SUNPHARMA.NS": ("Sun Pharmaceutical", "Healthcare"),
    "ULTRACEMCO.NS": ("UltraTech Cement", "Materials"),
}

TICKERS: list[str] = list(COMPANIES.keys())
