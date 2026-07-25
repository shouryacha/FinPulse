# FinPulse

FinPulse tracks 20 NSE-listed Indian companies and puts their price, fundamentals, and
history on a dashboard. There's a small FastAPI backend that pulls data from Yahoo
Finance on a schedule and stores it in a database, and a Streamlit frontend that reads
from the backend's REST API.

Built for the SoFI Core Induction — **AlgoLabs Assignment 1**.

- **Live dashboard:** https://finpulse-hdstc3fnmwdvitbyppb5jq.streamlit.app/
- **Backend API:** https://finpulse-api-5t6h.onrender.com

## Architecture

```
                    ┌─────────────────┐
  Yahoo Finance ───▶│  data_fetcher.py │  (yfinance)
                    └────────┬─────────┘
                             │ every ~15 min (APScheduler)
                             ▼
                    ┌─────────────────┐
                    │     database     │  (SQLite or Postgres)
                    │ companies        │
                    │ stock_snapshot   │
                    │ price_history    │
                    └────────┬─────────┘
                             │ SQLAlchemy
                             ▼
                    ┌─────────────────┐
                    │   FastAPI app    │  /stocks, /stocks/{ticker},
                    │  (backend/)      │  /stocks/{ticker}/history,
                    └────────┬─────────┘  /market-summary
                             │ REST (JSON over HTTPS)
                             ▼
                    ┌─────────────────┐
                    │ Streamlit app    │  Overview, Company Detail,
                    │  (frontend/)     │  Comparison, Sector View
                    └─────────────────┘
```

The backend is one FastAPI process. On startup it creates tables if they don't exist,
does an initial data pull, then a background job keeps re-fetching from yfinance on an
interval. The frontend only ever talks to the backend's REST API — it has no DB
credentials and never calls yfinance directly.

## Tech Stack

| Layer      | Technology                          |
|------------|--------------------------------------|
| Data       | yfinance (Yahoo Finance)             |
| Backend    | FastAPI, SQLAlchemy, APScheduler     |
| Database   | SQLite by default, swaps to Postgres if `DATABASE_URL` is set |
| Frontend   | Streamlit, Plotly                    |
| Deployment | Render (backend), Streamlit Community Cloud (frontend) |

## Project Structure

```
finpulse/
  backend/
    app/
      main.py             # FastAPI app + lifespan (create tables, initial refresh, scheduler)
      config.py            # tracked tickers, sector map, env-driven settings
      database.py           # SQLAlchemy engine/session
      models.py             # Company, StockSnapshot, PriceHistory ORM models
      schemas.py             # Pydantic response models
      data_fetcher.py         # yfinance wrapper: fetch + upsert snapshot & history
      scheduler.py             # APScheduler background refresh job
      routers/
        stocks.py               # /stocks, /stocks/{ticker}, /stocks/{ticker}/history
        market.py                # /market-summary, /refresh
    requirements.txt
    render.yaml
  frontend/
    streamlit_app.py     # Overview page (company table + market summary)
    pages/
      1_Company_Detail.py    # candlestick chart + fundamentals for one company
      2_Comparison.py          # multi-company indexed price overlay + P/E comparison
      3_Sector_View.py          # sector-wise market cap / P/E comparison
    utils/api_client.py     # requests wrapper around the backend REST API
    .streamlit/config.toml    # dark theme
  report/one_pager.md     # project report (architecture, challenges, future work)
```

## Running Locally

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# optional: without DATABASE_URL set, this just uses a local SQLite file
cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

First startup fetches fundamentals + 1y of history for all 20 tickers, which takes
30-60 seconds — you'll see `Initial refresh done: 20 succeeded, 0 failed` in the logs
when it's ready.

Check it worked: open `http://127.0.0.1:8000/stocks`.

### 2. Frontend

```bash
cd frontend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # points at localhost:8000 by default

streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

## REST API

| Endpoint                          | Description                                              |
|------------------------------------|-----------------------------------------------------------|
| `GET /stocks`                      | All tracked companies with their latest snapshot          |
| `GET /stocks/{ticker}`             | Single company's latest snapshot (e.g. `RELIANCE.NS`)     |
| `GET /stocks/{ticker}/history?days=365` | Daily OHLCV bars for charting                        |
| `GET /market-summary`              | Aggregate stats: total market cap, avg P/E, gainers/losers, top mover |
| `POST /refresh`                    | Manually triggers a data refresh (also runs automatically) |

FastAPI auto-generates interactive docs at `/docs` on the running backend.

## Database Design

- **`companies`** — static reference data (ticker, name, sector) for the 20 tracked companies
- **`stock_snapshot`** — one row per ticker, upserted on every refresh. This is the
  "latest state" the dashboard reads for price/market cap/P/E/EPS
- **`price_history`** — daily OHLCV bars, backfilled once per ticker (1 year of history)

Snapshot and history live in separate tables because they get written to differently:
snapshot rows get overwritten every refresh cycle, history rows only ever get inserted.

## Features Implemented

- Live + historical data for 20 NSE companies (price, market cap, P/E, EPS, volume, day change)
- Scheduled background refresh, so the dashboard never blocks on a live yfinance call
- 5 REST endpoints (only 3 were required)
- 4-page dashboard: Overview table with sector/name filtering, per-company candlestick
  chart, multi-company indexed-price + P/E comparison, and a sector-wise comparison view
- Volume overlay under the candlestick chart, colored to match each day's move
- Custom stock screener (price / P/E / market-cap range sliders) on the Overview page
- Dark mode by default

## Challenges Faced

The gnarliest bug: `yfinance`'s `fast_info` object only answers `.get()` with camelCase
keys (`lastPrice`, `marketCap`), but the actual values live under snake_case attributes
(`fast_info.last_price`). Calling `.get("last_price")` doesn't error, it just quietly
returns `None`, so every field looked "fetched" while actually being empty. Only caught
this by checking the real API response end to end instead of trusting a code read-through.

Database choice was more of a late scramble than a clean decision. The plan was Supabase
Postgres, but its direct connection string turned out to be IPv6-only, which isn't
reachable from this network — Supabase does offer a connection-pooler URL that works over
IPv4, but chasing that down wasn't worth it against the deadline. Shipped with SQLite on
Render instead. That's fine here mainly because the app re-seeds its data from yfinance on
every startup anyway, so there's no real data-loss risk from Render's ephemeral disk —
swapping in a real Postgres URL later is just an env var away (`DATABASE_URL`).

Also had to decide what "live" actually means given free hosting: hitting yfinance for
all 20 tickers on every dashboard load would be slow and would probably get rate-limited
eventually, so the backend treats "live" as "cached in the DB and refreshed every ~15 min"
instead of fetching on demand.

## Future Improvements

- WebSocket/SSE push instead of Streamlit's cache-based polling, for actually-live updates
- More fundamental ratios (ROE, debt/equity, dividend yield)
- User-defined watchlists instead of a fixed 20-company list
- Email/Telegram alerts on price or P/E thresholds
- Getting the Postgres connection working properly instead of relying on SQLite

## AI Tools Used

Built with help from **Claude Code** (Anthropic) — scaffolding, debugging (including the
yfinance issue above), and drafting this README/report. I've gone through and tested
every part and can walk through any of it.
