import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# Page Config
st.set_page_config(page_title="📊 Stock AI + Nifty Indicators", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

# Stock Input
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

# Stock Data Section
if ticker:
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or 'Close' not in df.columns:
            st.error("⚠️ Could not fetch stock data.")
        else:
            df = df[['Close']].dropna()

            if len(df) < 20:
                st.warning("⚠️ Not enough data for indicators.")
            else:
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                delta = df['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / avg_loss
                df['RSI'] = 100 - (100 / (1 + rs))
                df.dropna(inplace=True)

                latest = df.iloc[-1]
                st.subheader("📊 Latest Technical Data")
                st.write(f"**Current Price:** ₹{latest['Close']:.2f}")
                st.write(f"**SMA-20:** ₹{latest['SMA20']:.2f}")
                st.write(f"**RSI (14-day):** {latest['RSI']:.2f}")

                if latest['Close'] > latest['SMA20'] and latest['RSI'] < 70:
                    st.success("🟢 **Buy Signal** – Momentum looks strong.")
                elif latest['Close'] < latest['SMA20'] and latest['RSI'] > 30:
                    st.error("🔴 **Sell Signal** – Weak price action.")
                else:
                    st.info("⚪ **Hold** – Trend unclear.")

                st.line_chart(df[['Close', 'SMA20']])
    except Exception as e:
        st.error("❌ App crashed. Here's the error:")
        st.code(str(e))

# ----------------------------
# 📈 Nifty 50 Call/Put OI
# ----------------------------
st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators")

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
        session.get("https://www.nseindia.com", timeout=5)
        time.sleep(1)
        res = session.get(url, timeout=5)
        return res.json()
    except Exception:
        return None

nse_data = fetch_nifty_options()
if nse_data:
    try:
        records = nse_data['records']['data']
        filtered = [item for item in records if 'CE' in item and 'PE' in item]
        total_call_oi = sum(i['CE']['openInterest'] for i in filtered if 'CE' in i)
        total_put_oi = sum(i['PE']['openInterest'] for i in filtered if 'PE' in i)
        pcr = total_put_oi / total_call_oi if total_call_oi else 0

        st.write(f"📊 **Put/Call Ratio (PCR):** `{pcr:.2f}`")
        st.write(f"🔴 **Total Call OI:** {total_call_oi:,}")
        st.write(f"🟢 **Total Put OI:** {total_put_oi:,}")

        st.markdown("### 🔥 Top Resistance Levels (Call OI)")
        top_calls = sorted(filtered, key=lambda x: x['CE']['openInterest'], reverse=True)[:3]
        for item in top_calls:
            st.write(f"₹{item['strikePrice']} → {item['CE']['openInterest']:,}")

        st.markdown("### 🛡️ Top Support Levels (Put OI)")
        top_puts = sorted(filtered, key=lambda x: x['PE']['openInterest'], reverse=True)[:3]
        for item in top_puts:
            st.write(f"₹{item['strikePrice']} → {item['PE']['openInterest']:,}")

    except Exception as e:
        st.error("⚠️ Could not process Nifty data.")
        st.code(str(e))
else:
    st.warning("❌ Failed to load Nifty data. NSE may have blocked access.")
