import pandas as pd
import streamlit as st

from utils.api_client import get_market_summary, get_stocks

st.set_page_config(page_title="FinPulse | Overview", page_icon="\U0001F4C8", layout="wide")

st.title("FinPulse")
st.caption("A monitoring dashboard for 20 NSE-listed Indian companies — live price, fundamentals & comparison.")

try:
    stocks = get_stocks()
    summary = get_market_summary()
except Exception as exc:
    st.error(
        "Could not reach the FinPulse API. Is the backend running and is `BACKEND_URL` set correctly?\n\n"
        f"Details: {exc}"
    )
    st.stop()

if not stocks:
    st.warning("No stock data yet — the backend may still be running its first data refresh. Try again shortly.")
    st.stop()

df = pd.DataFrame(stocks)

# --- Market summary strip ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tracked Companies", summary["tracked_companies"])
c2.metric("Total Market Cap", f"₹{summary['total_market_cap'] / 1e12:.2f} Lakh Cr")
c3.metric("Average P/E", f"{summary['average_pe_ratio']:.1f}" if summary["average_pe_ratio"] else "n/a")
c4.metric("Gainers / Losers", f"{summary['gainers']} ↑  /  {summary['losers']} ↓")

top_col1, top_col2 = st.columns(2)
if summary["top_gainer"]:
    tg = summary["top_gainer"]
    top_col1.success(f"**Top Gainer:** {tg['name']} ({tg['ticker']}) ↑ {tg['day_change_pct']:.2f}%")
if summary["top_loser"]:
    tl = summary["top_loser"]
    top_col2.error(f"**Top Loser:** {tl['name']} ({tl['ticker']}) ↓ {abs(tl['day_change_pct']):.2f}%")

st.divider()

# --- Filters ---
sectors = ["All"] + sorted(df["sector"].unique().tolist())
selected_sector = st.selectbox("Filter by sector", sectors)
filtered = df if selected_sector == "All" else df[df["sector"] == selected_sector]

search = st.text_input("Search by name or ticker", "")
if search:
    mask = filtered["name"].str.contains(search, case=False, na=False) | filtered["ticker"].str.contains(
        search, case=False, na=False
    )
    filtered = filtered[mask]

# --- Company table ---
display_df = filtered.rename(
    columns={
        "ticker": "Ticker",
        "name": "Company",
        "sector": "Sector",
        "price": "Price (₹)",
        "day_change_pct": "Day Change %",
        "market_cap": "Market Cap (₹)",
        "pe_ratio": "P/E",
        "eps": "EPS (₹)",
        "volume": "Volume",
    }
)[
    ["Ticker", "Company", "Sector", "Price (₹)", "Day Change %", "Market Cap (₹)", "P/E", "EPS (₹)", "Volume"]
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
        "Day Change %": st.column_config.NumberColumn(format="%.2f%%"),
        "Market Cap (₹)": st.column_config.NumberColumn(format="compact"),
        "P/E": st.column_config.NumberColumn(format="%.1f"),
        "EPS (₹)": st.column_config.NumberColumn(format="₹%.2f"),
        "Volume": st.column_config.NumberColumn(format="compact"),
    },
)

st.caption(
    "Data source: Yahoo Finance (yfinance), refreshed on the backend every ~15 minutes. "
    "Use the sidebar pages for per-company detail, multi-company comparison, and a sector view."
)
