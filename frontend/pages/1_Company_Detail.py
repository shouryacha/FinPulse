import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.api_client import get_history, get_stocks

st.set_page_config(page_title="FinPulse | Company Detail", page_icon="\U0001F50E", layout="wide")
st.title("Company Detail")

stocks = get_stocks()
if not stocks:
    st.warning("No stock data available yet.")
    st.stop()

options = {f"{s['name']} ({s['ticker']})": s for s in sorted(stocks, key=lambda s: s["name"])}
label = st.selectbox("Choose a company", list(options.keys()))
stock = options[label]
ticker = stock["ticker"]

period_days = st.radio("Chart period", [30, 90, 180, 365], index=3, horizontal=True, format_func=lambda d: f"{d}d")

# --- Fundamentals ---
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Price", f"₹{stock['price']:.2f}" if stock["price"] else "n/a", f"{stock['day_change_pct']:.2f}%")
m2.metric("Market Cap", f"₹{stock['market_cap'] / 1e7:.0f} Cr" if stock["market_cap"] else "n/a")
m3.metric("P/E Ratio", f"{stock['pe_ratio']:.1f}" if stock["pe_ratio"] else "n/a")
m4.metric("EPS", f"₹{stock['eps']:.2f}" if stock["eps"] else "n/a")
m5.metric("Sector", stock["sector"])

# --- Candlestick chart ---
history = get_history(ticker, days=period_days)
if not history:
    st.info("No historical price data available for this company yet.")
    st.stop()

hist_df = pd.DataFrame(history)
hist_df["trade_date"] = pd.to_datetime(hist_df["trade_date"])

fig = go.Figure(
    data=[
        go.Candlestick(
            x=hist_df["trade_date"],
            open=hist_df["open"],
            high=hist_df["high"],
            low=hist_df["low"],
            close=hist_df["close"],
            increasing_line_color="#2E8B57",
            decreasing_line_color="#C0392B",
            name=ticker,
        )
    ]
)
fig.update_layout(
    title=f"{stock['name']} — Historical Price ({period_days}d)",
    xaxis_title=None,
    yaxis_title="Price (₹)",
    xaxis_rangeslider_visible=False,
    height=500,
    margin=dict(l=10, r=10, t=50, b=10),
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("Show raw OHLCV data"):
    st.dataframe(hist_df, use_container_width=True, hide_index=True)
