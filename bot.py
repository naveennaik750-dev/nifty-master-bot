import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
import google.generativeai as genai

# --- 1. AI & THEME CONFIG ---
st.set_page_config(page_title="Nifty Master Pro", layout="wide")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Setup Required: Add GEMINI_API_KEY to Streamlit Cloud Secrets!")
    st.stop()

# --- 2. MULTI-PAGE NAVIGATION ---
with st.sidebar:
    st.title("🚀 Navigation Hub")
    page = st.radio("Switch View", ["Current Market", "Derivative Model"])
    interval = st.selectbox("Interval", ["1m", "5m", "15m", "1h"], index=2)
    st.divider()
    st.caption(f"Last Refreshed: {datetime.now().strftime('%H:%M:%S')}")

# --- 3. PAGE 1: CURRENT MARKET ---
if page == "Current Market":
    st.markdown("<h1 style='text-align: center;'>🌐 LIVE MARKET ANALYSIS</h1>", unsafe_allow_html=True)
    
    # Fetch Live Data
    nifty = yf.Ticker("^NSEI")
    hist = nifty.history(period="1d", interval=interval)
    
    if not hist.empty:
        ltp = hist['Close'].iloc[-1]
        change = ltp - hist['Open'].iloc[0]
        
        c1, c2 = st.columns(2)
        c1.metric("NIFTY 50", f"{ltp:.2f}", f"{change:+.2f}")
        c2.metric("Trend", "🟢 BULLISH" if change > 0 else "🔴 BEARISH")

        st.divider()
        st.subheader("🤖 AI Trade Logic (6 Targets)")
        prompt = f"Analyze Nifty at {ltp}. Suggest trade direction, Entry, SL, and 6 Targets (TP1-TP6)."
        st.markdown(f"```\n{model.generate_content(prompt).text}\n```")
        st.line_chart(hist['Close'])

# --- 4. PAGE 2: DERIVATIVE MODEL SHEET ---
else:
    st.markdown("<h1 style='text-align: center; color: #cc0000;'>📊 DERIVATIVE MODEL SHEET</h1>", unsafe_allow_html=True)
    
    # Live Data Simulation for the Sheet
    df_data = {
        "STRIKE": [24300, 24350, 24400, 24450, 24500],
        "CALL OI CHG": [45000, -12000, 89000, 110000, 230000],
        "PUT OI CHG": [98000, 76000, 44000, -5000, 1200]
    }
    df = pd.DataFrame(df_data)

    def style_oi(val):
        color = 'background-color: #008000; color: white' if val > 0 else 'background-color: #ff4b4b; color: white'
        return color

    col_call, col_put = st.columns(2)
    with col_call:
        st.success("🟢 NIFTY CALL OPTIONS")
        # FIXED: Using .map() instead of .applymap()
        st.dataframe(df[['STRIKE', 'CALL OI CHG']].style.map(style_oi, subset=['CALL OI CHG']), use_container_width=True, hide_index=True)
        
    with col_put:
        st.error("🔴 NIFTY PUT OPTIONS")
        st.dataframe(df[['STRIKE', 'PUT OI CHG']].style.map(style_oi, subset=['PUT OI CHG']), use_container_width=True, hide_index=True)

    # 6-Point Metrics Analysis
    st.divider()
    st.subheader("📑 6-Point Master Metrics")
    m1, m2, m3 = st.columns(3)
    m1.info("1️⃣ PCR: 0.86\n\n2️⃣ EMA: BUY")
    m2.write("3️⃣ OI: SELL\n\n4️⃣ VOL: SELL")
    m3.warning("5️⃣ GAMMA: WATCH\n\n6️⃣ VWAP: SELL")

time.sleep(60)
st.rerun()
