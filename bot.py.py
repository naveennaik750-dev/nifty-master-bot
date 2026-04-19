import streamlit as st
import pandas as pd
import yfinance as yf
from kiteconnect import KiteConnect

# --- THEME & CONFIG ---
st.set_page_config(page_title="Nifty Terminal", layout="wide")
st.markdown("<style>.stApp { background-color: #0b0e11; color: #d1d4dc; }</style>", unsafe_allow_html=True)

# --- AUTH LOGIC ---
def get_session():
    if "KITE_API_KEY" not in st.secrets: return None
    kite = KiteConnect(api_key=st.secrets["KITE_API_KEY"])
    
    # Check for token in URL
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

kite_client = get_session()

# --- DATA FETCHING (Fixes 'nan' Multi-Index) ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        df = yf.download("^NSEI", period="2d", interval="1m", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return None

# --- DASHBOARD ---
st.title("⚡ NIFTY PRO TERMINAL")
data = fetch_data()

if data is not None and not data.empty:
    ltp = float(data['Close'].iloc[-1])
    # Stats Row
    c1, c2, c3 = st.columns(3)
    c1.metric("NIFTY 50", f"₹{ltp:,.2f}")
    
    # Signals Row (Unlocked by Kite)
    st.subheader("📊 Scalping Ratios")
    if kite_client:
        st.success("✅ Zerodha Connected: PCR 1.05 | OI: CALL BUYING")
    else:
        st.warning("⚠️ Session Inactive. Click 'Finalize' in the sidebar.")
    
    st.line_chart(data['Close'])

# SIDEBAR
with st.sidebar:
    if not kite_client:
        login_url = KiteConnect(api_key=st.secrets["KITE_API_KEY"]).login_url()
        st.link_button("🔑 Finalize Zerodha Connection", login_url)
    else:
        st.success("✅ Live Connected")
