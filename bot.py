import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
import google.generativeai as genai
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. PRO UI CONFIGURATION ---
st.set_page_config(page_title="Nifty Master Pro", layout="wide", initial_sidebar_state="expanded")

# Custom Professional CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0b0e11; border-right: 1px solid #2b2f36; }
    .stApp { background-color: #0b0e11; color: #d1d4dc; }
    .metric-card { background: #161a1e; padding: 15px; border-radius: 10px; border: 1px solid #2b2f36; }
    div[data-testid="stMetricValue"] { color: #ffffff; font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ AI Key Missing in Secrets")
    st.stop()

# --- 2. OPTIMIZED DATA ENGINE ---
@st.cache_data(ttl=300)
def get_nifty_ohlc(tf):
    try:
        data = yf.download("^NSEI", period="1d", interval=tf, progress=False)
        return data
    except:
        return pd.DataFrame()

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=80)
    st.markdown("<h2 style='color:white;'>PRO TERMINAL</h2>", unsafe_allow_html=True)
    page = st.selectbox("Switch Workspace", ["Live Terminal", "Derivative Sheet"])
    tf = st.selectbox("Interval", ["1m", "5m", "15m", "1h"], index=1)
    st.divider()
    st.caption(f"Sync: {datetime.now().strftime('%H:%M:%S')}")

# --- 4. WORKSPACE: LIVE TERMINAL ---
if page == "Live Terminal":
    # Top Metrics Row
    data = get_nifty_ohlc(tf)
    if not data.empty:
        ltp = float(data['Close'].iloc[-1])
        change = ltp - float(data['Open'].iloc[0])
        
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("NIFTY 50", f"{ltp:,.2f}", f"{change:+.2f}")
        with m2: st.metric("TREND", "BULLISH" if change > 0 else "BEARISH")
        with m3: st.metric("VOLATILITY", "HIGH" if abs(change) > 50 else "STABLE")

    st.divider()
    
    # Angel One Style Chart
    st.markdown("### 📈 Real-Time Candlestick Analysis")
    if not data.empty:
        df = data.reset_index()
        df.columns = ['time', 'open', 'high', 'low', 'close', 'adj', 'vol']
        df['time'] = df['time'].astype(int) // 10**9
        
        chart_data = df[['time', 'open', 'high', 'low', 'close']].to_dict('records')
        
        c_options = {
            "layout": {"backgroundColor": "#0b0e11", "textColor": "#d1d4dc"},
            "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#1f2226"}},
            "rightPriceScale": {"borderColor": "#2b2f36"},
            "timeScale": {"borderColor": "#2b2f36", "timeVisible": True}
        }
        
        series = [{
            "type": 'Candlestick',
            "data": chart_data,
            "options": {"upColor": "#089981", "downColor": "#f23645", "borderVisible": False}
        }]
        
        renderLightweightCharts(series=series, options=c_options, height=500)

    # Gemini AI Trade Suggester
    st.divider()
    st.markdown("### 🤖 Gemini AI Trade Signal")
    with st.container():
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        if st.button("Generate Scalp Setup"):
            # Applying your specific trading rules
            prompt = f"Nifty LTP {ltp}. Trade under $5, SL $2. Give 6 targets."
            st.write(ai_model.generate_content(prompt).text)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. WORKSPACE: DERIVATIVE SHEET ---
else:
    st.markdown("## 📑 Weekly Option Chain Sheet")
    # Simulation of the side-by-side table from your images
    col_c, col_p = st.columns(2)
    
    dummy_data = {
        "STRIKE": [24300, 24350, 24400, 24450],
        "OI CHANGE": [450000, -120000, 890000, 230000]
    }
    df_sheet = pd.DataFrame(dummy_data)

    def pro_style(val):
        color = '#089981' if val > 0 else '#f23645'
        return f'color: {color}; font-weight: bold; border-left: 3px solid {color}'

    with col_c:
        st.markdown("<h4 style='color:#089981;'>CALL DATA</h4>", unsafe_allow_html=True)
        st.dataframe(df_sheet.style.map(pro_style, subset=['OI CHANGE']), use_container_width=True)
    
    with col_p:
        st.markdown("<h4 style='color:#f23645;'>PUT DATA</h4>", unsafe_allow_html=True)
        st.dataframe(df_sheet.style.map(pro_style, subset=['OI CHANGE']), use_container_width=True)

# Auto-refresh optimized for Rate Limits
time.sleep(300)
st.rerun()
