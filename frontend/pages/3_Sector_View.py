import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.api_client import get_stocks

st.set_page_config(page_title="FinPulse | Sector View", page_icon="\U0001F3E2", layout="wide")
st.title("Sector-wise Comparison")

stocks = get_stocks()
if not stocks:
    st.warning("No stock data available yet.")
    st.stop()

df = pd.DataFrame(stocks)

sector_summary = (
    df.groupby("sector")
    .agg(
        companies=("ticker", "count"),
        total_market_cap=("market_cap", "sum"),
        avg_pe=("pe_ratio", "mean"),
        avg_day_change=("day_change_pct", "mean"),
    )
    .reset_index()
    .sort_values("total_market_cap", ascending=False)
)

col1, col2 = st.columns(2)

with col1:
    fig_cap = go.Figure(
        data=[
            go.Bar(
                x=sector_summary["sector"],
                y=sector_summary["total_market_cap"] / 1e7,
                marker_color="#4C78A8",
            )
        ]
    )
    fig_cap.update_layout(
        title="Total Market Cap by Sector",
        yaxis_title="Market Cap (₹ Cr)",
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(fig_cap, use_container_width=True)

with col2:
    fig_pe = go.Figure(
        data=[
            go.Bar(
                x=sector_summary["sector"],
                y=sector_summary["avg_pe"],
                marker_color="#54A24B",
            )
        ]
    )
    fig_pe.update_layout(
        title="Average P/E Ratio by Sector",
        yaxis_title="Average P/E",
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(fig_pe, use_container_width=True)

st.divider()
st.subheader("Sector Summary Table")
display = sector_summary.rename(
    columns={
        "sector": "Sector",
        "companies": "Companies",
        "total_market_cap": "Total Market Cap (₹)",
        "avg_pe": "Avg P/E",
        "avg_day_change": "Avg Day Change %",
    }
)
st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Total Market Cap (₹)": st.column_config.NumberColumn(format="compact"),
        "Avg P/E": st.column_config.NumberColumn(format="%.1f"),
        "Avg Day Change %": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

st.divider()
st.subheader("Companies by Sector")
selected_sector = st.selectbox("Drill into a sector", sorted(df["sector"].unique().tolist()))
sector_companies = df[df["sector"] == selected_sector][
    ["ticker", "name", "price", "day_change_pct", "market_cap", "pe_ratio", "eps"]
].rename(
    columns={
        "ticker": "Ticker",
        "name": "Company",
        "price": "Price (₹)",
        "day_change_pct": "Day Change %",
        "market_cap": "Market Cap (₹)",
        "pe_ratio": "P/E",
        "eps": "EPS (₹)",
    }
)
st.dataframe(sector_companies, use_container_width=True, hide_index=True)
