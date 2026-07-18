# FinPulse — Project Report

**AlgoLabs Assignment 1, SoFI Core Induction**

## Project Architecture

FinPulse is a three-tier application: a scheduled data-fetching layer, a REST API
backend, and a dashboard frontend, kept as two independently deployable services.

1. **Data layer** (`backend/app/data_fetcher.py`): pulls live price/fundamentals and
   historical OHLCV bars from Yahoo Finance (`yfinance`) for 20 NSE-listed companies.
   An APScheduler background job re-runs this every ~15 minutes inside the FastAPI
   process, so the dashboard never blocks on an external API call.
2. **Backend** (`backend/`): FastAPI app backed by a Postgres database (Supabase). It
   exposes the stored data as JSON over 5 REST endpoints and owns all data-fetching and
   persistence logic.
3. **Frontend** (`frontend/`): a Streamlit multi-page app that only calls the backend's
   REST API — it never talks to the database or Yahoo Finance directly. This keeps the
   two halves independently deployable (Render for the API, Streamlit Community Cloud
   for the dashboard) and mirrors a typical client/server split.

## APIs Used

- **Yahoo Finance**, via the `yfinance` Python library — live quotes (`fast_info`) and
  fundamentals (`.info`: trailing P/E, trailing EPS) plus historical daily OHLCV bars.
- **FinPulse's own REST API** (built for this project): `GET /stocks`, `GET
  /stocks/{ticker}`, `GET /stocks/{ticker}/history`, `GET /market-summary`, `POST
  /refresh` — consumed exclusively by the Streamlit frontend.

## Database Design

Postgres (Supabase), three tables:

- `companies` — static reference data: ticker (PK), name, sector.
- `stock_snapshot` — one row per ticker (latest-state cache: price, day change %, market
  cap, P/E, EPS, volume, last-updated timestamp), **upserted** every refresh cycle.
- `price_history` — append-only daily OHLCV bars per ticker, unique on (ticker, date),
  backfilled once (1 year) and extended on later refreshes. Powers the candlestick and
  comparison charts.

Snapshot and history are modeled separately because they have different write patterns:
snapshot rows are overwritten in place, history rows are only ever appended.

## Features Implemented

- Live + historical tracking for 20 Nifty50 constituents across 10 sectors
- 5 REST endpoints (minimum required was 3)
- Dashboard: sortable/filterable Overview table, per-company candlestick chart with
  selectable time range, multi-company indexed-price comparison + P/E bar chart, and a
  sector-wise comparison view (bonus)
- Dark mode by default (bonus)
- Deployed end-to-end: Supabase (DB) → Render (API) → Streamlit Community Cloud (dashboard)

## Challenges Faced

The trickiest bug was in the data-fetching layer: `yfinance`'s `FastInfo.get()` method
only recognizes camelCase keys (`lastPrice`, `marketCap`), while the object's attributes
are snake_case (`last_price`, `market_cap`). Calling `.get("last_price")` silently
returned `None` instead of raising an error, so every field looked "fetched" but was
empty — this only surfaced when the actual API response was inspected end-to-end rather
than trusted from a code read-through, which is now the standing verification habit for
this project (curl every endpoint, don't just check that the process started).

The second design decision was around what "live" means on free hosting: fetching all 20
tickers on every page load would be slow and would hammer Yahoo Finance's undocumented
rate limits, so the backend treats "live" as "refreshed on a fixed schedule and cached in
Postgres," which also means the deployed app keeps working even if Yahoo Finance is briefly
unreachable.

## Future Improvements

- Push-based updates (WebSocket/SSE) instead of cache-based polling from the frontend
- More fundamental ratios (ROE, debt-to-equity, dividend yield) and technical indicators
- User-configurable watchlists instead of a fixed company universe
- Price/valuation alerting via email or Telegram
