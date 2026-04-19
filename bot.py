import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
import google.generativeai as genai

# --- 1. PRO TERMINAL THEME & CONFIG ---
st.set_page_config(page_title="Nifty Master Pro Ultra", layout="wide")

# Neon Professional Styling
st.markdown("""
    <style>
    .stApp { background-color: #06090d; color: #e1e4e8; }
    [data-testid="stMetricValue"] { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    .stAlert { background-color: #12171d; border: 1px solid #30363d; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# AI Setup with Safety Wrapper
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Setup Required: Add GEMINI_API_KEY to Streamlit Cloud Secrets!")
    st.stop()

# --- 2. MULTI-PAGE NAVIGATION (Sidebar) ---
with st.sidebar:
    st.title("🚀 Alpha Navigation")
    page = st.radio("Switch View", ["Current Market", "Derivative Model"])
    interval = st.selectbox("Interval", ["1m", "5m", "15m", "1h"], index=0)
    
    st.divider()
    # ADD-ON: Live News Ticker in Sidebar
    st.subheader("📰 Market Pulse")
    try:
        news = yf.Ticker("^NSEI").news[:3]
        for item in news:
            st.caption(f"**{item.get('publisher', 'NSE')}**")
            st.write(f"[{item.get('title', 'Market Update')}]({item.get('link', '#')})")
    except: st.caption("News sync pending...")
    
    st.divider()
    st.caption(f"Last Refreshed: {datetime.now().strftime('%H:%M:%S')}")

# --- HELPER: DATA ENGINE ---
def get_nifty_data(tf):
    try:
        df = yf.download("^NSEI", period="2d", interval=tf, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

# --- 3. PAGE 1: CURRENT MARKET (Improved with Tech Indicators) ---
if page == "Current Market":
    st.markdown("<h1 style='text-align: center;'>🌐 LIVE MARKET ANALYSIS</h1>", unsafe_allow_html=True)
    
    hist = get_nifty_data(interval)
    
    if not hist.empty:
        ltp = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[0]
        change = ltp - open_price
        
        # ADD-ON: Technical Indicator Calculations
        ema21 = hist['Close'].ewm(span=21).mean().iloc[-1]
        # RSI Calculation (14 Period)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # Top Metric Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("NIFTY 50", f"{ltp:.2f}", f"{change:+.2f}")
        c2.metric("EMA 21", f"{ema21:.1f}")
        c3.metric("RSI (14)", f"{rsi:.1f}")
        c4.metric("Trend", "🟢 BULLISH" if ltp > ema21 else "🔴 BEARISH")

        st.divider()
        
        # AI Trade Logic (TP1-TP6)
        st.subheader("🤖 AI Quantum Signal (Master Targets)")
        try:
            prompt = f"Nifty at {ltp}. RSI: {rsi:.1f}. Trend: {'Bullish' if ltp > ema21 else 'Bearish'}. Suggest: Direction, Entry, SL, and 6 Targets (TP1-TP6)."
            response = model.generate_content(prompt)
            st.info(response.text)
        except: st.warning("AI Overloaded. Scalping default: Watch for EMA 21 crossover.")
        
        st.line_chart(hist['Close'], height=400)

# --- 4. PAGE 2: DERIVATIVE MODEL (Improved with Heatmap) ---
else:
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>📊 DERIVATIVE MODEL SHEET</h1>", unsafe_allow_html=True)
    
    # Live Data Simulation
    df_data = {
        "STRIKE": [24300, 24350, 24400, 24450, 24500],
        "CALL OI CHG": [45000, -12000, 89000, 110000, 230000],
        "PUT OI CHG": [98000, 76000, 44000, -5000, 1200]
    }
    df = pd.DataFrame(df_data)

    def style_oi(val):
        # ADD-ON: Heatmap Logic
        if val > 100000: return 'background-color: #800000; color: white' # High Resistance
        if val > 50000: return 'background-color: #004d00; color: white' # Strong Support
        return 'color: #00ffcc'

    col_call, col_put = st.columns(2)
    with col_call:
        st.success("🟢 NIFTY CALL OPTIONS (Resistance)")
        st.dataframe(df[['STRIKE', 'CALL OI CHG']].style.map(style_oi, subset=['CALL OI CHG']), use_container_width=True, hide_index=True)
        
    with col_put:
        st.error("🔴 NIFTY PUT OPTIONS (Support)")
        st.dataframe(df[['STRIKE', 'PUT OI CHG']].style.map(style_oi, subset=['PUT OI CHG']), use_container_width=True, hide_index=True)

    # ADD-ON: 6-Point Master Metrics Expanded
    st.divider()
    st.subheader("📑 6-Point Master Execution Check")
    m_cols = st.columns(6)
    metrics = [
        ("PCR", "0.86", "Bearish"),
        ("EMA", "BUY", "Above"),
        ("OI", "SELL", "Heavy Call"),
        ("VOL",
