import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
import google.generativeai as genai

# --- 1. PRO CONFIG & THEME ---
st.set_page_config(page_title="Nifty Master Pro", layout="wide")

# Custom CSS for a professional trading floor look
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; color: #d1d4dc; }
    [data-testid="stMetricValue"] { color: #00ffcc !important; }
    .stRadio > label { color: #00ffcc !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- AI CONFIG WITH FALLBACK ---
def get_ai_model():
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return None
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

model = get_ai_model()

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🚀 Alpha Hub")
    page = st.radio("Navigation", ["Current Market", "Derivative Model"])
    interval = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h"], index=0) # Default to 1m for scalping
    st.divider()
    if st.button("Force Refresh"):
        st.rerun()
    st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")

# --- HELPER: DATA CLEANER ---
def fetch_nifty_data(tf):
    try:
        # period="1d" for fast loading
        df = yf.download("^NSEI", period="1d", interval=tf, progress=False)
        # CRITICAL: Fix Multi-Index 'nan' error
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

# --- 3. PAGE 1: LIVE ANALYSIS ---
if page == "Current Market":
    st.markdown("<h1 style='text-align: center;'>🌐 LIVE SCALPING TERMINAL</h1>", unsafe_allow_html=True)
    
    hist = fetch_nifty_data(interval)
    
    if not hist.empty:
        ltp = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[0]
        change = ltp - open_price
        
        # Performance Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("NIFTY 50", f"₹{ltp:,.2f}", f"{change:+.2f}")
        
        # Technical Logic: EMA 21 & VWAP
        ema21 = hist['Close'].ewm(span=21).mean().iloc[-1]
        m2.metric("EMA 21", f"{ema21:.1f}")
        
        trend_status = "🟢 BULLISH" if ltp > ema21 else "🔴 BEARISH"
        m3.metric("Trend Strength", trend_status)

        st.divider()
        
        # AI Trade Logic Section
        st.subheader("🤖 AI Signal Generator (Master Targets)")
        if model:
            try:
                # Prompt optimized for 6 targets as requested
                prompt = f"Current Nifty: {ltp:.2f}. Trend: {trend_status}. Give: 1. Trade Direction, 2. Entry Zone, 3. Stop Loss, 4. 6 Profit Targets (TP1-TP6). Keep it concise."
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e:
                st.warning("AI Busy. Using Technical Default: Watch EMA 21 crossover.")
        else:
            st.error("Missing GEMINI_API_KEY in Secrets.")

        st.line_chart(hist['Close'], height=400)
    else:
        st.error("Market data stream offline. Check internet or market hours.")

# --- 4. PAGE 2: DERIVATIVE MODEL ---
else:
    st.markdown("<h1 style='text-align: center; color: #00ffcc;'>📊 DERIVATIVE MONITOR</h1>", unsafe_allow_html=True)
    
    # Static Simulation - In a real app, you'd pull this from an Option Chain API
    df_data = {
        "STRIKE": [24300, 24350, 24400, 24450, 24500],
        "CALL OI CHG": [45000, -12000, 89000, 110000, 230000],
        "PUT OI CHG": [98000, 76000, 44000, -5000, 1200]
    }
    df = pd.DataFrame(df_data)

    def style_oi(val):
        return 'color: #00ffcc' if val > 0 else 'color: #ff4b4b'

    c_call, c_put = st.columns(2)
    with c_call:
        st.subheader("📞 Call Side (Resistance)")
        st.dataframe(df[['STRIKE', 'CALL OI CHG']].style.map(style_oi, subset=['CALL OI CHG']), use_container_width=True, hide_index=True)
        
    with c_put:
        st.subheader("📉 Put Side (Support)")
        st.dataframe(df[['STRIKE', 'PUT OI CHG']].style.map(style_oi, subset=['PUT OI CHG']), use_container_width=True, hide_index=True)

    # 6-Point Master Metrics
    st.divider()
    st.subheader("📑 6-Point Execution Check")
    cols = st.columns(6)
    metrics = [
        ("PCR", "0.86", "Bearish"),
        ("EMA", "Buy", "Above"),
        ("OI", "Sell", "Heavy Call"),
        ("VOL", "High", "Spike"),
        ("GAMMA", "Watch", "Neutral"),
        ("VWAP", "Sell", "Below")
    ]
    for i, (label, val, desc) in enumerate(metrics):
        cols[i].metric(label, val, desc)

# Auto-refresh logic
time.sleep(30)
st.rerun()
