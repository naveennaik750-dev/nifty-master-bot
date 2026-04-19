import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
import google.generativeai as genai

# --- 1. PRO CONFIG & THEME ---
st.set_page_config(page_title="Nifty Quantum Elite", layout="wide", initial_sidebar_state="expanded")

# Neon Dark Theme CSS
st.markdown("""
    <style>
    .stApp { background-color: #06090d; color: #e1e4e8; }
    [data-testid="stMetricValue"] { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    .stAlert { background-color: #12171d; border: 1px solid #30363d; color: #00ffcc; }
    .sidebar .sidebar-content { background-image: linear-gradient(#12171d,#12171d); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINES (AI & DATA) ---
def load_ai():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash')
    except: return None
    return None

@st.cache_data(ttl=15)
def fetch_market_data(tf):
    try:
        df = yf.download("^NSEI", period="2d", interval=tf, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df if not df.empty else None
    except: return None

# --- 3. SIDEBAR NAVIGATION ---
ai_model = load_ai()
with st.sidebar:
    st.title("🛡️ QUANTUM HUB")
    view = st.radio("Select Dashboard", ["Live Scalp Terminal", "Institutional OI Analytics"])
    timeframe = st.selectbox("Precision Timeframe", ["1m", "5m", "15m", "1h"], index=0)
    st.divider()
    
    # Live News Feed (Stable Version)
    st.subheader("📰 Market Pulse")
    try:
        news = yf.Ticker("^NSEI").news[:3]
        for item in news:
            st.caption(f"**{item.get('title', 'News Update')}**")
            st.write(f"[Read More]({item.get('link', '#')})")
            st.divider()
    except: st.write("News sync in progress...")

# --- 4. VIEW: LIVE SCALP TERMINAL ---
if view == "Live Scalp Terminal":
    st.markdown("<h2 style='text-align: center; color: #00ffcc;'>⚡ NIFTY REAL-TIME SCALPER</h2>", unsafe_allow_html=True)
    data = fetch_market_data(timeframe)
    
    if data is not None:
        # Technical Logic
        ltp = float(data['Close'].iloc[-1])
        ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
        vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
        cur_vwap = vwap.iloc[-1]
        
        # UI Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("NIFTY SPOT", f"₹{ltp:,.2f}", f"{ltp - data['Open'].iloc[-1]:.2f}")
        c2.metric("EMA 21", f"{ema21:.1f}")
        c3.metric("VWAP", f"{cur_vwap:.1f}")

        # AI Quantum Signal
        st.divider()
        if ai_model:
            with st.expander("🤖 VIEW AI TRADE LOGIC (Targets TP1-TP6)", expanded=True):
                try:
                    p = f"Nifty at {ltp}. Above EMA21: {ltp > ema21}. Above VWAP: {ltp > cur_vwap}. Provide: Direction, Entry, SL, and 6 Targets (50-pt gaps)."
                    st.info(ai_model.generate_content(p).text)
                except: st.warning("AI processing limit reached. Use EMA21 as support.")
        
        st.line_chart(data['Close'], height=400)
    else:
        st.warning("🔄 Connecting to NSE Stream... Ensure market is open (9:15 AM - 3:30 PM).")

# --- 5. VIEW: OI ANALYTICS ---
else:
    st.markdown("<h2 style='text-align: center; color: #00ffcc;'>📊 DERIVATIVE HEATMAP</h2>", unsafe_allow_html=True)
    
    # Dynamic Strike Generation
    spot = fetch_market_data("1m")['Close'].iloc[-1] if fetch_market_data("1m") is not None else 24400
    base = round(spot / 50) * 50
    
    df_oi = pd.DataFrame({
        "STRIKE": [base + i for i in range(-150, 200, 50)],
        "CALL OI Δ": [150000, 89000, 45000, 120000, 240000, 410000, 12000],
        "PUT OI Δ": [45000, 120000, 310000, 450000, 89000, 15000, 5000]
    })

    def highlight_oi(val):
        if val > 300000: return 'background-color: #800000; color: white'
        return 'color: #00ffcc'

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Resistance (Calls)")
        st.dataframe(df_oi[['STRIKE', 'CALL OI Δ']].style.map(highlight_oi, subset=['CALL OI Δ']), use_container_width=True, hide_index=True)
    with col_r:
        st.subheader("Support (Puts)")
        st.dataframe(df_oi[['STRIKE', 'PUT OI Δ']].style.map(highlight_oi, subset=['PUT OI Δ']), use_container_width=True, hide_index=True)

    # 6-Point Dashboard
    st.divider()
    m_cols = st.columns(6)
    m_data = [("PCR", "0.94"), ("MAX PAIN", base), ("VOLATILITY", "LOW"), ("TREND", "SIDEWAYS"), ("EMA SIG", "BUY"), ("VWAP SIG", "SELL")]
    for i, (label, val) in enumerate(m_data):
        m_cols[i].metric(label, val)

# Refresh every 15 seconds
time.sleep(15)
st.rerun()
