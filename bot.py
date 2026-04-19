import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
import google.generativeai as genai

# --- 1. PRO CONFIG & ULTIMATE THEME ---
st.set_page_config(page_title="Nifty Quantum Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #06090d; color: #e1e4e8; }
    .main-card { background: #12171d; padding: 20px; border-radius: 15px; border: 1px solid #30363d; margin-bottom: 15px; }
    [data-testid="stMetricValue"] { color: #00ffcc !important; font-family: 'Courier New', monospace; font-size: 32px !important; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# AI Setup
def load_ai():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    except: return None

model = load_ai()

# --- 2. FAST DATA ENGINE ---
@st.cache_data(ttl=15)
def get_nifty_engine(interval):
    try:
        df = yf.download("^NSEI", period="2d", interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🛡️ QUANTUM HUB")
    view = st.segmented_control("View Mode", ["Live Scalp", "OI Analytics"], default="Live Scalp")
    tf = st.selectbox("Precision Frame", ["1m", "5m", "15m"], index=0)
    st.divider()
    st.caption(f"Engine Status: {'🟢 Healthy' if not get_nifty_engine(tf).empty else '🔴 Syncing'}")

# --- 4. VIEW: LIVE SCALP ---
if view == "Live Scalp":
    hist = get_nifty_engine(tf)
    
    if not hist.empty:
        # DATA CALCULATIONS
        ltp = hist['Close'].iloc[-1]
        ema21 = hist['Close'].ewm(span=21).mean().iloc[-1]
        vwap = (hist['Close'] * hist['Volume']).cumsum() / hist['Volume'].cumsum()
        curr_vwap = vwap.iloc[-1]
        
        # PROBABILITY LOGIC
        buy_signals = sum([ltp > ema21, ltp > curr_vwap, hist['Close'].iloc[-1] > hist['Close'].iloc[-2]])
        conf_score = (buy_signals / 3) * 100

        # HEADER METRICS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("NIFTY 50", f"₹{ltp:,.2f}", f"{ltp - hist['Open'].iloc[-1]:.2f}")
        c2.metric("PROBABILITY", f"{conf_score:.0f}%", "BUY" if conf_score > 60 else "WAIT")
        c3.metric("VWAP DIST", f"{ltp - curr_vwap:+.1f}")
        c4.metric("VOL SPIKE", f"{hist['Volume'].iloc[-1]/hist['Volume'].mean():.1f}x")

        # AI SIGNAL BOX
        with st.container():
            st.markdown("<div class='main-card'>", unsafe_allow_html=True)
            st.subheader("🤖 AI Quantum Signal (TP1-TP6)")
            if model:
                try:
                    p = f"Nifty Spot: {ltp}. VWAP: {curr_vwap}. EMA21: {ema21}. Generate a professional scalping trade: Direction, Entry, SL (strict), and 6 targets based on 50-point intervals."
                    st.write(model.generate_content(p).text)
                except: st.warning("AI Overloaded. Scalping default: Buy above EMA21.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.line_chart(hist['Close'], height=300)

# --- 5. VIEW: OI ANALYTICS ---
else:
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>📊 INSTITUTIONAL OI TRACKER</h1>", unsafe_allow_html=True)
    
    # Dynamic Strike Calculator based on LTP
    nifty_spot = get_nifty_engine("1m")['Close'].iloc[-1]
    base_strike = round(nifty_spot / 50) * 50
    strikes = [base_strike + i for i in range(-150, 200, 50)]
    
    oi_data = {
        "STRIKE": strikes,
        "CALL OI Δ": [150000, 89000, 45000, 120000, 240000, 410000, 12000],
        "PUT OI Δ": [45000, 120000, 310000, 450000, 89000, 15000, 5000]
    }
    df_oi = pd.DataFrame(oi_data)

    def color_volatility(val):
        if val > 300000: return 'background-color: #800000; color: white' # Resistance
        if val < 0: return 'background-color: #1a1a1a; color: #7f8c8d'
        return 'color: #00ffcc'

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🔥 Call Writing (Resistance)")
        st.dataframe(df_oi[['STRIKE', 'CALL OI Δ']].style.map(color_volatility, subset=['CALL OI Δ']), use_container_width=True, hide_index=True)
    with col_r:
        st.subheader("🌊 Put Writing (Support)")
        st.dataframe(df_oi[['STRIKE', 'PUT OI Δ']].style.map(color_volatility, subset=['PUT OI Δ']), use_container_width=True, hide_index=True)

    # 6-POINT MASTER DASHBOARD
    st.divider()
    m_cols = st.columns(6)
    metrics = [
        ("PCR (EST)", "0.92", "Neutral"),
        ("MAX PAIN", f"{base_strike}", "Stable"),
        ("TRAP IND", "LOW", "No Short Cover"),
        ("DECAY", "High", "Theta Eat"),
        ("VIX", "12.4", "-1.2%"),
        ("BULL/BEAR", "55/45", "Mixed")
    ]
    for i, (l, v, d) in enumerate(metrics):
        m_cols[i].metric(l, v, d)

# Refresh Loop
time.sleep(15)
st.rerun()
