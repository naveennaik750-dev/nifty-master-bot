import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime

# --- 1. PRO TERMINAL THEME ---
st.set_page_config(page_title="Nifty Pro Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #d1d4dc; }
    .metric-card { background: #161a1e; padding: 15px; border-radius: 10px; border: 1px solid #2d3339; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE DATA ENGINE (Broker-Free) ---
@st.cache_data(ttl=2) # Refreshes every 2 seconds
def get_live_nifty():
    try:
        # Fetching Nifty 50 Spot
        ticker = yf.Ticker("^NSEI")
        df = ticker.history(period="1d", interval="1m")
        
        # Fixing the Multi-Index 'nan' error
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if not df.empty:
            return df
        return None
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return None

# --- 3. MAIN INTERFACE ---
st.title("⚡ NIFTY 50 REAL-TIME TERMINAL")
st.write(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

data = get_live_nifty()

if data is not None:
    # 4. CALCULATION ENGINE
    ltp = float(data['Close'].iloc[-1])
    prev_close = float(data['Open'].iloc[0])
    change = ltp - prev_close
    pct_change = (change / prev_close) * 100
    
    # Requirements: EMA & VWAP
    ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    cur_vwap = vwap.iloc[-1]

    # TOP METRICS
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("NIFTY 50", f"₹{ltp:,.2f}", f"{change:+.2f} ({pct_change:+.2f}%)")
    with c2:
        st.metric("EMA 21", f"{ema21:.1f}")
    with c3:
        st.metric("VWAP", f"{cur_vwap:.1f}")
    with c4:
        # Since we removed Zerodha, we use Volume Intensity as a proxy for OI
        vol_ratio = data['Volume'].iloc[-1] / data['Volume'].mean()
        st.metric("VOL INTENSITY", f"{vol_ratio:.2f}x")

    # 5. SCALPING SIGNALS (Logic-Based)
    st.subheader("📊 Scalping Ratios (Live)")
    s1, s2, s3 = st.columns(3)
    
    # Signal 1: Trend
    if ltp > ema21 and ltp > cur_vwap:
        s1.success("SIGNAL: STRONG BULLISH")
    elif ltp < ema21 and ltp < cur_vwap:
        s1.error("SIGNAL: STRONG BEARISH")
    else:
        s1.warning("SIGNAL: SIDEWAYS / NEUTRAL")

    # Signal 2: Volume
    if vol_ratio > 1.5:
        s2.info("VOLUME: SPIKE DETECTED")
    else:
        s2.write("VOLUME: NORMAL")

    # Signal 3: Price Action
    st.line_chart(data['Close'], height=400)

else:
    st.warning("Waiting for Market Stream... Ensure it is market hours (9:15 AM - 3:30 PM IST).")

# 6. AUTO-REFRESH
time.sleep(1) # Faster update for real-time feel
st.rerun()
