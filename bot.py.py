import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime

# --- 1. PRO TERMINAL THEME ---
st.set_page_config(page_title="Nifty Live Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #d1d4dc; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LIVE DATA ENGINE (No Secrets Needed) ---
def get_market_data():
    try:
        # Fetching Nifty 50 Index Spot
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False)
        
        # Flattening columns to prevent the 'nan' error
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df if not df.empty else None
    except Exception as e:
        st.error(f"Waiting for stream... {e}")
        return None

# --- 3. MAIN INTERFACE ---
st.title("⚡ NIFTY 50 PRO REAL-TIME")
st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')} (Broker-Free Stream)")

data = get_market_data()

if data is not None:
    # 4. TECH CALCULATION
    ltp = float(data['Close'].iloc[-1])
    ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
    
    # VWAP Calculation (Price * Volume / Total Volume)
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    cur_vwap = vwap.iloc[-1]

    # TOP METRICS ROW
    c1, c2, c3 = st.columns(3)
    c1.metric("NIFTY LTP", f"₹{ltp:,.2f}")
    c2.metric("EMA 21", f"{ema21:.1f}")
    c3.metric("VWAP", f"{cur_vwap:.1f}")

    # 5. SCALPING SIGNALS
    st.subheader("📊 Scalping Analysis")
    s1, s2 = st.columns(2)
    
    # Trend Logic
    if ltp > ema21 and ltp > cur_vwap:
        s1.success("SIGNAL: BULLISH (Buy on Dips)")
    elif ltp < ema21 and ltp < cur_vwap:
        s1.error("SIGNAL: BEARISH (Sell on Rise)")
    else:
        s1.warning("SIGNAL: SIDEWAYS (No Trade)")

    # Volume Intensity
    vol_avg = data['Volume'].tail(10).mean()
    curr_vol = data['Volume'].iloc[-1]
    if curr_vol > (vol_avg * 1.5):
        s2.info("VOLUME: SPIKE DETECTED")
    else:
        s2.write("VOLUME: NORMAL")

    # CHART
    st.line_chart(data['Close'], height=400)

else:
    st.info("Market is currently closed or data is syncing. Data resumes at 9:15 AM IST.")

# 6. AUTO-REFRESH (Every 5 seconds)
time.sleep(5)
st.rerun()
