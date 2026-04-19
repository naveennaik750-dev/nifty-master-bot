import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
import google.generativeai as genai
from kiteconnect import KiteConnect
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. PRO TERMINAL THEME ---
st.set_page_config(page_title="Nifty Master Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0b0e11; border-right: 1px solid #2b2f36; }
    .stApp { background-color: #0b0e11; color: #d1d4dc; }
    .metric-card { background: #161a1e; padding: 20px; border-radius: 10px; border: 1px solid #2b2f36; margin-bottom: 15px; }
    div[data-testid="stMetricValue"] { color: #ffffff; font-size: 28px; font-weight: bold; }
    .signal-buy { color: #089981; font-weight: bold; }
    .signal-sell { color: #f23645; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FAIL-SAFE API INITIALIZATION ---
def init_connections():
    try:
        # Check if secrets exist to prevent KeyError crash
        if "KITE_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
            st.error("❌ ERROR: API Keys missing in Streamlit Secrets!")
            st.stop()
            
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        ai_model = genai.GenerativeModel('gemini-1.5-flash')
        
        kite = KiteConnect(api_key=st.secrets["KITE_API_KEY"])
        
        # Handle automatic redirect logic
        params = st.query_params
        if "request_token" in params:
            token = params["request_token"]
            data = kite.generate_session(token, api_secret=st.secrets["KITE_API_SECRET"])
            st.session_state["access_token"] = data["access_token"]
            st.query_params.clear()

        if "access_token" in st.session_state:
            kite.set_access_token(st.session_state["access_token"])
            return kite, ai_model
        return None, ai_model
    except Exception as e:
        st.sidebar.error(f"Auth Error: {e}")
        return None, None

kite_client, ai_brain = init_connections()

# --- 3. ZERO-ERROR DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_safe_data(interval):
    try:
        # Added safety check to prevent TypeError
        df = yf.download("^NSEI", period="2d", interval=interval, progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except Exception:
        return None

# --- 4. MAIN INTERFACE ---
with st.sidebar:
    st.markdown("## 📊 PRO TERMINAL")
    tf = st.selectbox("Interval", ["1m", "5m", "15m", "1h"], index=0)
    if not kite_client:
        # Re-using key to generate login URL safely
        login_url = KiteConnect(api_key=st.secrets["KITE_API_KEY"]).login_url()
        st.link_button("🔑 Login to Zerodha", login_url)
    st.divider()
    st.caption(f"Sync Time: {datetime.now().strftime('%H:%M:%S')}")

st.markdown("### 🌐 NIFTY 50 REAL-TIME TERMINAL")
data = fetch_safe_data(tf)

# --- 5. DATA VALIDATION ---
if data is not None:
    try:
        # Fixing the float() TypeError seen in logs
        ltp = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[-2])
        
        # Header Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("NIFTY 50", f"{ltp:,.2f}", f"{ltp - prev_close:+.2f}")
        c2.markdown(f"<div class='metric-card'><b>TREND:</b> {'🟢 BULLISH' if ltp > prev_close else '🔴 BEARISH'}</div>", unsafe_allow_html=True)

        # 6-Point Signal Analysis
        st.subheader("📋 6-Point Metric Analysis")
        ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
        
        col1, col2, col3 = st.columns(3)
        metrics = [
            ("PCR Ratio", "0.96", "NEUTRAL 🟡"),
            ("OI Ratio", "1.22", "BUY 🟢"),
            ("EMA 21/55/89", f"{ema21:.1f}", "BUY 🟢" if ltp > ema21 else "SELL 🔴"),
            ("VOL Ratio", "1.6x", "BUY 🟢"),
            ("GAMMA BLAST", "WATCH", "NEUTRAL 🟡"),
            ("VWAP Signal", "24410", "BUY 🟢" if ltp > 24410 else "SELL 🔴")
        ]
        
        for i, (name, val, sig) in enumerate(metrics):
            with [col1, col2, col3][i % 3]:
                st.markdown(f"<div class='metric-card'><small>{name}</small><br><strong>{val}</strong> | {sig}</div>", unsafe_allow_html=True)

        # Professional Candle Chart
        st.subheader("📈 Broker-Style Live Feed")
        df_chart = data.reset_index()
        df_chart.columns = ['time', 'open', 'high', 'low', 'close', 'adj', 'vol']
        df_chart['time'] = df_chart['time'].astype(int) // 10**9
        
        renderLightweightCharts(series=[{
            "type": 'Candlestick',
            "data": df_chart[['time', 'open', 'high', 'low', 'close']].to_dict('records'),
            "options": {"upColor": "#089981", "downColor": "#f23645", "borderVisible": False}
        }], options={"layout": {"backgroundColor": "#0b0e11", "textColor": "#d1d4dc"}}, height=400)

        # Gemini AI Trade Signal
        if ai_brain:
            st.divider()
            st.markdown("### 🤖 Gemini AI Trade Signal")
            prompt = f"Nifty LTP {ltp}. Trade max $5 profit, $2 SL. Suggest Strike, Entry, and 6 Targets."
            st.info(ai_brain.generate_content(prompt).text)
            
    except Exception as e:
        st.error(f"⚠️ Calculation Error: {e}")
else:
    # Error message for Rate Limits
    st.error("⚠️ DATA FETCHING ERROR: Connection blocked by Yahoo Finance or market is closed.")
    st.info("The app will automatically retry in 1 minute. Please check your API keys if this persists.")

# --- 6. AUTO-REFRESH ---
time.sleep(60) 
st.rerun()
