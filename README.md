# FinPulse

A stock market monitoring platform that tracks 20 NSE-listed Indian companies, storing
live and historical market data in a database and surfacing it through a REST API and an
interactive dashboard.

Built for the SoFI Core Induction — **AlgoLabs Assignment 1**.

- **Live dashboard:** _add Streamlit Community Cloud URL here after deploying_
- **Backend API:** _add Render URL here after deploying_

## Architecture

```
                    ┌─────────────────┐
  Yahoo Finance ───▶│  data_fetcher.py │  (yfinance)
                    └────────┬─────────┘
                             │ every ~15 min (APScheduler)
                             ▼
                    ┌─────────────────┐
                    │   Postgres DB    │  (Supabase)
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

The backend is a single FastAPI process. On startup it creates tables (if needed), runs
an initial data refresh, and starts a background job that re-pulls data from yfinance on
an interval. The frontend is a separate Streamlit app that only talks to the backend over
its public REST API — it holds no database credentials and does no direct data fetching.

## Tech Stack

| Layer      | Technology                          |
|------------|--------------------------------------|
| Data       | yfinance (Yahoo Finance)             |
| Backend    | FastAPI, SQLAlchemy, APScheduler     |
| Database   | PostgreSQL (Supabase), SQLite for local dev |
| Frontend   | Streamlit, Plotly                    |
| Deployment | Render (backend), Streamlit Community Cloud (frontend), Supabase (DB) |

## Project Structure

```
finpulse/
  backend/
    app/
      main.py          # FastAPI app + lifespan (create tables, initial refresh, scheduler)
      config.py         # tracked tickers, sector map, env-driven settings
      database.py        # SQLAlchemy engine/session
      models.py          # Company, StockSnapshot, PriceHistory ORM models
      schemas.py          # Pydantic response models
      data_fetcher.py      # yfinance wrapper: fetch + upsert snapshot & history
      scheduler.py          # APScheduler background refresh job
      routers/
        stocks.py            # /stocks, /stocks/{ticker}, /stocks/{ticker}/history
        market.py             # /market-summary, /refresh
    requirements.txt
    render.yaml
  frontend/
    streamlit_app.py    # Overview page (company table + market summary)
    pages/
      1_Company_Detail.py   # candlestick chart + fundamentals for one company
      2_Comparison.py         # multi-company indexed price overlay + P/E comparison
      3_Sector_View.py         # sector-wise market cap / P/E comparison
    utils/api_client.py    # requests wrapper around the backend REST API
    .streamlit/config.toml   # dark theme
  report/one_pager.md    # project report (architecture, challenges, future work)
```

## Running Locally

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: without DATABASE_URL set, it falls back to a local SQLite file.
cp .env.example .env           # then edit DATABASE_URL if you have a Postgres instance

uvicorn app.main:app --reload --port 8000
```

The first startup fetches fundamentals + 1y of history for all 20 tickers, which can take
30-60 seconds — watch the terminal for `Initial refresh done: 20 succeeded, 0 failed`.

Verify it's working: open `http://127.0.0.1:8000/stocks` in a browser.

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

Interactive API docs are auto-generated by FastAPI at `/docs` on the running backend.

## Database Design

- **`companies`** — static reference data (ticker, name, sector) for the 20 tracked companies.
- **`stock_snapshot`** — one row per ticker, upserted on every refresh cycle. This is the
  "latest state" cache the dashboard reads for price/market cap/P/E/EPS.
- **`price_history`** — append-only daily OHLCV bars, backfilled once per ticker (1 year)
  and extended on later refresh cycles. Powers the candlestick and comparison charts.

Snapshot and history are separated because they have different write patterns: snapshot
rows are overwritten every refresh, history rows are only ever inserted.

## Features Implemented

- Live + historical data for 20 NSE companies (price, market cap, P/E, EPS, volume, day change)
- Postgres-backed storage with a scheduled background refresh (no manual re-fetching needed)
- 5 REST API endpoints (2 more than the minimum of 3 required)
- 4-page interactive dashboard: Overview table with sector/name filtering, per-company
  candlestick chart, multi-company indexed-price + P/E comparison, and a sector-wise
  comparison view
- Volume overlay beneath the candlestick chart, colored to match each day's move
- Custom stock screener (price / P/E / market-cap range sliders) on the Overview page
- Dark mode by default

## Challenges Faced

- `yfinance`'s `fast_info` object only responds to `.get()` with camelCase keys (e.g.
  `lastPrice`) but exposes snake_case via attribute access (`fast_info.last_price`) — this
  silently returned `None` for every field until caught during local testing against the
  live API responses, not just unit-level mocks.
- Free-tier hosting for the backend typically has an ephemeral filesystem, which rules out
  SQLite for the deployed app — hence Supabase Postgres, so data survives restarts/redeploys.
- Balancing "live" data against Yahoo Finance's request patterns: refreshing all 20 tickers
  synchronously on every dashboard page load would be slow and fragile, so the backend
  caches the latest snapshot in the database and refreshes it on a fixed interval instead.

## Future Improvements

- WebSocket or Server-Sent Events push from backend to frontend instead of Streamlit's
  cache-based polling, for truer "live" updates
- Additional fundamental ratios (ROE, debt/equity, dividend yield)
- User-defined custom watchlists instead of a fixed 20-company universe
- Alerting (email/Telegram) on price or P/E threshold breaches

## AI Tools Used

This project was built with assistance from **Claude Code** (Anthropic) for code
scaffolding, the yfinance debugging session described above, and drafting this README
and the one-page report. The applicant reviewed, tested, and can explain every component.
