import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# Page Config
st.set_page_config(page_title="Stock AI + Nifty Options", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

# User Input
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

# --- Stock Data & Analysis ---
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

        st.subheader("### 📊 Latest Technical Data")
        st.write(f"**Current Price:** ₹{current_price:.2f}")
        st.write(f"**SMA-20:** ₹{sma20:.2f}")
        st.write(f"**RSI (14-day):** {rsi:.2f}")

        signal = "⚪ Hold – Wait for better confirmation."
        if current_price > sma20 and rsi < 70:
            signal = "🟢 **Buy Signal** – Momentum looks strong."
        elif current_price < sma20 and rsi > 30:
            signal = "🔴 **Sell Signal** – Weak price action."

        st.subheader("### 🧠 AI Suggestion")
        st.markdown(signal)
        st.line_chart(df[['Close', 'SMA20']])

# --- Nifty Options Fetch Function ---
@st.cache_data(ttl=3600)
def get_nifty_options():
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com"
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        # NSE requires a home page visit first
        session.get("https://www.nseindia.com", timeout=5)
        time.sleep(1)  # Delay to simulate browser
        response = session.get(url, timeout=5)
        return response
    except Exception as e:
        return None

# --- Nifty 50 Options Data Display ---
st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators (Options Data)")

response = get_nifty_options()
if response and response.status_code == 200:
    try:
        data = response.json()
        records = data['records']['data']
        ce_data = [item for item in records if 'CE' in item and 'PE' in item]
        
        total_ce_oi = sum(item['CE']['openInterest'] for item in ce_data)
        total_pe_oi = sum(item['PE']['openInterest'] for item in ce_data)
        pcr = total_pe_oi / total_ce_oi if total_ce_oi else 0

        top_ce = sorted(ce_data, key=lambda x: x['CE']['openInterest'], reverse=True)[:3]
        top_pe = sorted(ce_data, key=lambda x: x['PE']['openInterest'], reverse=True)[:3]

        st.write(f"📊 **Put/Call Ratio (PCR):** `{pcr:.2f}`")
        st.write(f"🔴 **Total Call OI:** {total_ce_oi:,}")
        st.write(f"🟢 **Total Put OI:** {total_pe_oi:,}")

        st.markdown("### 🔴 Top 3 Resistance (Call OI)")
        for item in top_ce:
            st.write(f"₹{item['strikePrice']} → {item['CE']['openInterest']:,}")

        st.markdown("### 🟢 Top 3 Support (Put OI)")
        for item in top_pe:
            st.write(f"₹{item['strikePrice']} → {item['PE']['openInterest']:,}")

    except Exception as e:
        st.error("❌ Failed to fetch Nifty 50 options data.")
        st.text(f"Error: {str(e)}")
        st.text(response.text[:200])
else:
    st.error("❌ Failed to load Nifty 50 options data.")
    if response:
        st.text(f"HTTP Error: {response.status_code}")
