import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

# --- 1. PRO TERMINAL THEME ---
st.set_page_config(page_title="Nifty Pro Terminal", layout="wide")
st.markdown("<style>.stApp { background-color: #0b0e11; color: #d1d4dc; }</style>", unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
def get_live_data():
    try:
        # 1-Minute Time Frame for Scalping
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df if not df.empty else None
    except:
        return None

# --- 3. NEWS FEED ENGINE ---
def get_market_news():
    try:
        # Pulls latest 5 news headlines for Nifty
        nifty = yf.Ticker("^NSEI")
        return nifty.news[:5] 
    except:
        return []

# --- 4. MAIN INTERFACE ---
st.title("⚡ NIFTY 50 LIVE TERMINAL")
data = get_live_data()
news = get_market_news()

# Sidebar for News Updates
with st.sidebar:
    st.header("📰 Live Market News")
    for item in news:
        st.write(f"**{item['publisher']}**")
        st.write(f"[{item['title']}]({item['link']})")
        st.divider()

if data is not None:
    ltp = float(data['Close'].iloc[-1])
    ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("NIFTY LTP", f"₹{ltp:,.2f}")
    c2.metric("EMA 21", f"{ema21:.1f}")
    c3.metric("VWAP", f"{vwap.iloc[-1]:.1f}")

    st.line_chart(data['Close'], height=350)
else:
    st.info("Syncing 1m Time Frame... Terminal will update shortly.")

# Auto-Refresh
time.sleep(10)
st.rerun()
