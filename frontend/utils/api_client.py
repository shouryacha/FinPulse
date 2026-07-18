"""Thin wrapper around the FinPulse REST API for the Streamlit pages to share."""

import os

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=120)
def get_stocks() -> list[dict]:
    resp = requests.get(f"{BACKEND_URL}/stocks", timeout=15)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=120)
def get_stock(ticker: str) -> dict:
    resp = requests.get(f"{BACKEND_URL}/stocks/{ticker}", timeout=15)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=300)
def get_history(ticker: str, days: int = 365) -> list[dict]:
    resp = requests.get(f"{BACKEND_URL}/stocks/{ticker}/history", params={"days": days}, timeout=15)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=120)
def get_market_summary() -> dict:
    resp = requests.get(f"{BACKEND_URL}/market-summary", timeout=15)
    resp.raise_for_status()
    return resp.json()
