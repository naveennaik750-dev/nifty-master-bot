import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

# --- 1. PRO TERMINAL THEME ---
st.set_page_config(page_title="Nifty Live Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #d1d4dc; }
    [data-testid="stMetricValue"] { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LIVE DATA ENGINE ---
def get_clean_data():
    try:
        # Fetching Nifty 50 Index
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False)
        
        # Fixing the Multi-Index error that causes 'nan'
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df if not df.empty else None
    except:
        return None

# --- 3. MAIN INTERFACE ---
st.title("⚡ NIFTY 50 REAL-TIME")
st.caption(f"Status: Live Broker-Free Stream | Sync: {datetime.now().strftime('%H:%M:%S')}")

data = get_clean_data()

if data is not None:
    # Calculation Engine
    ltp = float(data['Close'].iloc[-1])
    ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    cur_vwap = vwap.iloc[-1]

    # TOP METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric("NIFTY LTP", f"₹{ltp:,.2f}")
    c2.metric("EMA 21", f"{ema21:.1f}")
    c3.metric("VWAP", f"{cur_vwap:.1f}")

    # SCALPING SIGNALS
    st.subheader("📊 Live Scalping Analysis")
    col_a, col_b = st.columns(2)
    
    # Trend Logic
    if ltp > ema21 and ltp > cur_vwap:
        col_a.success("STRATEGY: STRONG BULLISH")
    elif ltp < ema21 and ltp < cur_vwap:
        col_a.error("STRATEGY: STRONG BEARISH")
    else:
        col_a.warning("STRATEGY: NEUTRAL/SIDEWAYS")

    # Volume Spike Detection
    vol_avg = data['Volume'].tail(10).mean()
    if data['Volume'].iloc[-1] > (vol_avg * 1.5):
        col_b.info("VOLUME: SPIKE ALERT ⚡")
    else:
        col_b.write("Volume: Normal")

    st.line_chart(data['Close'], height=350)

else:
    st.info("Syncing data... The terminal will update automatically every few seconds.")

# --- 4. AUTO-REFRESH ---
time.sleep(10)
st.rerun()
