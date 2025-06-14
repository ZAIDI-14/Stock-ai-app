import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# Page Config
st.set_page_config(page_title="Stock AI + Nifty Indicators", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

# User Input
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

# Stock Data + Technical Indicators
if ticker:
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or 'Close' not in df.columns:
        st.error("⚠️ Could not fetch stock data. Please check the ticker symbol.")
    else:
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        delta = df['Close'].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        latest = df.dropna().iloc[-1]
        current_price = latest['Close']
        sma20 = latest['SMA20']
        rsi = latest['RSI']

        st.subheader("📊 Latest Technical Data")
        st.write(f"**Current Price:** ₹{current_price:.2f}")
        st.write(f"**SMA-20:** ₹{sma20:.2f}")
        st.write(f"**RSI (14-day):** {rsi:.2f}")

        # Signal
        if current_price > sma20 and rsi < 70:
            signal = "🟢 **Buy Signal** – Momentum looks strong."
        elif current_price < sma20 and rsi > 30:
            signal = "🔴 **Sell Signal** – Weak price action."
        else:
            signal = "⚪ **Hold** – Trend unclear."

        st.subheader("🧠 AI Suggestion")
        st.markdown(signal)

        # Chart
        st.line_chart(df[['Close', 'SMA20']].dropna())

# --- Nifty Options Function ---
@st.cache_data(ttl=3600)
def fetch_nifty_options():
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com"
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        # Required to simulate browser
        session.get("https://www.nseindia.com", timeout=5)
        time.sleep(1)
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

# --- Nifty 50 Call/Put OI Display ---
st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators (Options Data)")

nse_data = fetch_nifty_options()

if nse_data:
    try:
        records = nse_data['records']['data']
        filtered = [item for item in records if 'CE' in item and 'PE' in item]
        total_call_oi = sum(i['CE']['openInterest'] for i in filtered)
        total_put_oi = sum(i['PE']['openInterest'] for i in filtered)
        pcr = total_put_oi / total_call_oi if total_call_oi else 0

        # Top strikes
        top_calls = sorted(filtered, key=lambda x: x['CE']['openInterest'], reverse=True)[:3]
        top_puts = sorted(filtered, key=lambda x: x['PE']['openInterest'], reverse=True)[:3]

        st.write(f"📊 **Put/Call Ratio (PCR):** `{pcr:.2f}`")
        st.write(f"🔴 **Total Call OI:** {total_call_oi:,}")
        st.write(f"🟢 **Total Put OI:** {total_put_oi:,}")

        st.markdown("### 🔴 Top 3 Resistance (Call OI)")
        for row in top_calls:
            st.write(f"₹{row['strikePrice']} → {row['CE']['openInterest']:,}")

        st.markdown("### 🟢 Top 3 Support (Put OI)")
        for row in top_puts:
            st.write(f"₹{row['strikePrice']} → {row['PE']['openInterest']:,}")

    except Exception as e:
        st.error("⚠️ Failed to process options data.")
        st.text(str(e))
else:
    st.error("❌ Failed to load Nifty 50 options data. NSE may be blocking access.")
