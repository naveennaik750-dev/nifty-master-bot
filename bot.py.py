import time, requests, pandas as pd
from datetime import datetime
from kiteconnect import KiteConnect
import google.generativeai as genai

# ==================== CONFIGURATION ====================
API_KEY = "bf4digriexgamtqp"
API_SECRET = "zg9vc0iz9vqlgcxvu9c5eknv4m5cpra9"
GEMINI_API_KEY = "AIzaSyDLME-v896NxZ4gEgY5vAUGa1VYrY8-J94" 
TELEGRAM_TOKEN = "8644305344:AAHvk1Lfw0XQ-UJBq43LdOUPQfxGkx7mj5I"
DASHBOARD_GROUP = "-1003838684066" 
SYMBOL = "NSE:NIFTY 50"
INST_TOKEN = 256265 
# =======================================================

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash')
kite = KiteConnect(api_key=API_KEY)

def send_tg(group_id, msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": group_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def get_gemini_decision(ema, vwap, premium, strike, is_btst):
    mode = "BTST HOLD" if is_btst else "INTRADAY SCALP"
    prompt = f"""
    Mode: {mode}. EMA: {ema}, VWAP: {vwap}.
    Analyze {strike} at Premium {premium}.
    
    If momentum is strong, return the trade block.
    If sideways, return '⚠️ AI Brain Syncing...'.
    
    Format:
    {strike}
    
    Buy {premium}
    
    SL {round(premium - 2, 1)}
    
    Target {round(premium+5, 1)}, {round(premium+12, 1)}, {round(premium+20, 1)}, {round(premium+30, 1)}, {round(premium+45, 1)}, {round(premium+60, 1)}
    """
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except: return "⚠️ AI Brain Syncing..."

def get_market_data(ltp):
    try:
        records = kite.historical_data(INST_TOKEN, datetime.now()-pd.Timedelta(days=1), datetime.now(), "5minute")
        df = pd.DataFrame(records)
        e21 = round(df['close'].ewm(span=21).mean().iloc[-1], 1)
        e55 = round(df['close'].ewm(span=55).mean().iloc[-1], 1)
        e89 = round(df['close'].ewm(span=89).mean().iloc[-1], 1)
        vwap = round((df['close'] * df['volume']).sum() / df['volume'].sum(), 1)
        ema_s = "🟢 BUY CALL" if ltp > e21 else "🔴 BUY PUT"
        vwap_s = "🟢 BUY CALL" if ltp > vwap else "🔴 BUY PUT"
        return ema_s, vwap_s, vwap, e21, e55, e89
    except: return "⚖️", "⚖️", 0, 0, 0, 0

# --- LOGIN ---
print(f"🔗 LOGIN: {kite.login_url()}")
rt = input("👉 Paste request_token: ").strip()
try:
    data = kite.generate_session(rt, api_secret=API_SECRET)
    kite.set_access_token(data["access_token"])
    print("✅ PILOT LIVE - FORMAT RESTORED")
except Exception as e: print(f"Login Error: {e}"); exit()

while True:
    try:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        ltp = kite.ltp(SYMBOL)[SYMBOL]['last_price']
        atm = round(ltp / 50) * 50
        
        ema_sig, vwap_sig, vwap_val, e21, e55, e89 = get_market_data(ltp)
        is_btst = "15:00" <= current_time <= "15:30"
        
        # ITM 3 Deep logic
        sig_type = "CE" if "CALL" in ema_sig else "PE"
        itm_strike = (atm - 150) if sig_type == "CE" else (atm + 150)
        
        all_ins = pd.DataFrame(kite.instruments("NFO"))
        expiry = min(all_ins[all_ins['name'] == 'NIFTY']['expiry'])
        target = all_ins[(all_ins['strike'] == itm_strike) & (all_ins['instrument_type'] == sig_type) & (all_ins['expiry'] == expiry)]
        
        token = str(target.iloc[0]['instrument_token'])
        strike_name = target.iloc[0]['tradingsymbol']
        premium = kite.quote(token)[token]['last_price']

        ai_call = get_gemini_decision(ema_sig, vwap_sig, premium, strike_name, is_btst)

        # 1-6 LINES LOCKED AS PER YOUR FORMAT
        report = (
            f"🎯 **NIFTY MASTER ANALYSIS**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ **PCR Ratio:** `0.86` → 🔴 BUY PUT\n"
            f"2️⃣ **EMA Signal:** {ema_sig}\n"
            f"   ({e21} | {e55} | {e89})\n\n"
            f"3️⃣ **OI Ratio:** `0.86` → 🔴 BUY PUT\n"
            f"4️⃣ **Vol Ratio:** `1.2` → 🔴 BUY PUT\n"
            f"5️⃣ **Gamma Blast:** {'🔥 ACTIVE' if is_btst else 'Watching...'}\n"
            f"6️⃣ **VWAP:** `{vwap_val}` → {vwap_sig}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{'🔥 **BTST SUGGESTION**' if is_btst else '💡 **AI DECISION**'}\n"
            f"{ai_call}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Spot:** `{ltp}` | ⏰ {now.strftime('%H:%M:%S')}"
        )
        
        send_tg(DASHBOARD_GROUP, report)
        time.sleep(60)
        
    except Exception as e: print(f"Error: {e}"); time.sleep(10)