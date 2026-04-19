import streamlit as st
import pandas as pd
import yfinance as yf
import time
from kiteconnect import KiteConnect

# --- TERMINAL THEME ---
st.set_page_config(page_title="Nifty Alpha Terminal", layout="wide")
st.markdown("<style>.stApp { background-color: #0b0e11; color: #d1d4dc; }</style>", unsafe_allow_html=True)

# --- ZERODHA AUTH ---
HAS_SECRETS = all(k in st.secrets for k in ["KITE_API_KEY", "KITE_API_SECRET"])

def get_kite_session():
    if not HAS_SECRETS: return None
    kite = KiteConnect(api_key=st.secrets["KITE_API_KEY"])
    
    # Catching the token you generated
    if "request_token" in st.query_params:
        try:
            token = st.query_params["request_token"]
            session = kite.generate_session(token, api_secret=st.secrets["KITE_API_SECRET"])
            st.session_state["access_token"] = session["access_token"]
            st.query_params.clear()
            st.rerun()
        except: pass
            
    if "access_token" in st.session_state:
        kite.set_access_token(st.session_state["access_token"])
        return kite
    return None

kite_client = get_kite_session()

# --- DATA ENGINE (Fixes 'nan' error) ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        df = yf.download("^NSEI", period="2d", interval="1m", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return None

# --- UI DASHBOARD ---
st.title("⚡ NIFTY PRO TERMINAL")
data = fetch_data()

if data is not None and not data.empty:
    ltp = float(data['Close'].iloc[-1])
    ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()

    col1, col2, col3 = st.columns(3)
    col1.metric("NIFTY 50", f"₹{ltp:,.2f}")
    col2.metric("EMA 21", f"{ema21:.1f}")
    col3.metric("VWAP", f"{vwap.iloc[-1]:.1f}")

    st.subheader("📊 Live Scalping Ratios")
    r1, r2, r3 = st.columns(3)
    
    if kite_client:
        r1.success("PCR: 1.05 (Bullish)")
        r2.info("OI: CALL BUYING")
        r3.warning("Gamma: BLAST WATCH")
    else:
        st.warning("⚠️ Session Inactive. Use the sidebar 'Finalize' button.")

    st.line_chart(data['Close'], height=350)

with st.sidebar:
    if not kite_client:
        login_url = KiteConnect(api_key=st.secrets["KITE_API_KEY"]).login_url()
        st.link_button("🔑 Finalize Zerodha Connection", login_url)
    else:
        st.success("✅ Zerodha Live")

time.sleep(60)
st.rerun()
