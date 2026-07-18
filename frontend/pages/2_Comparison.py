import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.api_client import get_history, get_stocks

st.set_page_config(page_title="FinPulse | Comparison", page_icon="\U0001F4CA", layout="wide")
st.title("Company Comparison")

stocks = get_stocks()
if not stocks:
    st.warning("No stock data available yet.")
    st.stop()

# Assign each ticker a color from a fixed palette based on its position in the
# full (alphabetically sorted) universe, so a ticker's color never changes just
# because the current selection changed -- color follows the entity, not its rank.
PALETTE = [
    "#4C78A8", "#F58518", "#54A24B", "#B279A2", "#E45756",
    "#72B7B2", "#EECA3B", "#FF9DA6", "#9D755D", "#BAB0AC",
]
all_tickers_sorted = sorted(s["ticker"] for s in stocks)
color_map = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(all_tickers_sorted)}

by_ticker = {s["ticker"]: s for s in stocks}
default_selection = all_tickers_sorted[:4]
selected = st.multiselect(
    "Select companies to compare (2-8 recommended)",
    options=all_tickers_sorted,
    default=default_selection,
    format_func=lambda t: f"{by_ticker[t]['name']} ({t})",
)

if len(selected) < 2:
    st.info("Pick at least two companies to compare.")
    st.stop()

period_days = st.radio("Comparison period", [30, 90, 180, 365], index=2, horizontal=True, format_func=lambda d: f"{d}d")

# --- Normalized price overlay (single axis: indexed return, base = 100) ---
fig = go.Figure()
for ticker in selected:
    hist = get_history(ticker, days=period_days)
    if not hist:
        continue
    hist_df = pd.DataFrame(hist)
    hist_df["trade_date"] = pd.to_datetime(hist_df["trade_date"])
    base = hist_df["close"].iloc[0]
    indexed = hist_df["close"] / base * 100
    fig.add_trace(
        go.Scatter(
            x=hist_df["trade_date"],
            y=indexed,
            mode="lines",
            name=f"{by_ticker[ticker]['name']} ({ticker})",
            line=dict(color=color_map[ticker], width=2),
        )
    )

fig.update_layout(
    title=f"Indexed Price Performance ({period_days}d, base = 100)",
    yaxis_title="Indexed Price (base = 100)",
    height=480,
    margin=dict(l=10, r=10, t=50, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Fundamentals comparison ---
comp_df = pd.DataFrame([by_ticker[t] for t in selected])
comp_df = comp_df[["ticker", "name", "sector", "price", "market_cap", "pe_ratio", "eps"]].rename(
    columns={
        "ticker": "Ticker",
        "name": "Company",
        "sector": "Sector",
        "price": "Price (₹)",
        "market_cap": "Market Cap (₹)",
        "pe_ratio": "P/E",
        "eps": "EPS (₹)",
    }
)
st.dataframe(comp_df, use_container_width=True, hide_index=True)

pe_fig = go.Figure(
    data=[
        go.Bar(
            x=[by_ticker[t]["ticker"] for t in selected],
            y=[by_ticker[t]["pe_ratio"] for t in selected],
            marker_color=[color_map[t] for t in selected],
        )
    ]
)
pe_fig.update_layout(
    title="P/E Ratio Comparison",
    yaxis_title="P/E Ratio",
    height=380,
    margin=dict(l=10, r=10, t=50, b=10),
    showlegend=False,
)
st.plotly_chart(pe_fig, use_container_width=True)
