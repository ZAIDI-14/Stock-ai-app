import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

st.set_page_config(page_title="📊 Stock AI + Nifty Indicators", layout="centered")
st.title("📈 Stock AI with Nifty 50 Call/Put Indicators")

ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

if ticker:
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or 'Close' not in df.columns:
            st.error("⚠️ Failed to fetch stock data.")
        else:
            df = df[['Close']].dropna()
            if len(df) < 20:
                st.warning("⚠️ Not enough data to calculate indicators.")
            else:
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                delta = df['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / avg_loss
                df['RSI'] = 100 - (100 / (1 + rs))
                df = df.dropna()

                latest = df.iloc[-1]
                st.subheader("📊 Technical Summary")
                st.write(f"**Price:** ₹{latest['Close']:.2f}")
                st.write(f"**SMA20:** ₹{latest['SMA20']:.2f}")
                st.write(f"**RSI:** {latest['RSI']:.2f}")

                # Signal
                if latest['Close'] > latest['SMA20'] and latest['RSI'] < 70:
                    st.success("🟢 Buy Signal")
                elif latest['Close'] < latest['SMA20'] and latest['RSI'] > 30:
                    st.error("🔴 Sell Signal")
                else:
                    st.info("⚪ Hold Signal")

                # Plot safe
                try:
                    st.line_chart(df[['Close', 'SMA20']])
                except Exception as plot_error:
                    st.warning("⚠️ Could not plot chart.")
                    st.code(str(plot_error))
    except Exception as e:
        st.error("❌ Stock Data Error:")
        st.code(str(e))

# -----------------------
# 📈 Nifty 50 Option Data
# -----------------------
st.markdown("---")
st.subheader("📊 Nifty 50 Call/Put OI Levels")

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
        filtered = [i for i in records if 'CE' in i and 'PE' in i]
        total_call_oi = sum(i['CE']['openInterest'] for i in filtered if 'CE' in i)
        total_put_oi = sum(i['PE']['openInterest'] for i in filtered if 'PE' in i)
        pcr = total_put_oi / total_call_oi if total_call_oi else 0

        st.write(f"**Put/Call Ratio:** {pcr:.2f}")
        st.write(f"🔴 Total Call OI: {total_call_oi:,}")
        st.write(f"🟢 Total Put OI: {total_put_oi:,}")

        st.markdown("### 🔺 Resistance (Call OI)")
        top_calls = sorted(filtered, key=lambda x: x['CE']['openInterest'], reverse=True)[:3]
        for i in top_calls:
            st.write(f"₹{i['strikePrice']} → {i['CE']['openInterest']:,}")

        st.markdown("### 🔻 Support (Put OI)")
        top_puts = sorted(filtered, key=lambda x: x['PE']['openInterest'], reverse=True)[:3]
        for i in top_puts:
            st.write(f"₹{i['strikePrice']} → {i['PE']['openInterest']:,}")

    except Exception as e:
        st.error("⚠️ Nifty option data error:")
        st.code(str(e))
else:
    st.warning("❌ NSE data fetch failed. Try again later.")
