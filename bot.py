import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

# --- 1. PRO TERMINAL THEME ---
st.set_page_config(page_title="Nifty Live Terminal", layout="wide")
st.markdown("<style>.stApp { background-color: #0b0e11; color: #d1d4dc; }</style>", unsafe_allow_html=True)

# --- 2. DATA ENGINE (1m Timeframe) ---
def get_live_data():
    try:
        # Fetches 1-minute intervals for today
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df if not df.empty else None
    except:
        return None

# --- 3. STABLE NEWS ENGINE (Fixes KeyError) ---
def get_market_news():
    try:
        nifty = yf.Ticker("^NSEI")
        raw_news = nifty.news[:5]
        return raw_news if raw_news else []
    except:
        return []

# --- 4. MAIN INTERFACE ---
st.title("⚡ NIFTY 50 LIVE TERMINAL")
data = get_live_data()
news_items = get_market_news()

# SIDEBAR NEWS
with st.sidebar:
    st.header("📰 Live Market News")
    if news_items:
        for item in news_items:
            # Safe way to get 'publisher' or 'title' without crashing
            source = item.get('publisher', 'Market Update')
            headline = item.get('title', 'No Title Available')
            link = item.get('link', '#')
            
            st.write(f"**{source}**")
            st.write(f"[{headline}]({link})")
            st.divider()
    else:
        st.write("No news updates at this moment.")

# PRICE DASHBOARD
if data is not None:
    ltp = float(data['Close'].iloc[-1])
    ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("NIFTY LTP", f"₹{ltp:,.2f}")
    c2.metric("EMA 21", f"{ema21:.1f}")
    c3.metric("VWAP", f"{vwap.iloc[-1]:.1f}")

    st.line_chart(data['Close'], height=350)
else:
    st.info("Market data is syncing. This terminal refreshes every 10 seconds.")

# AUTO-REFRESH
time.sleep(10)
st.rerun()
