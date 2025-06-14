import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# Page Setup
st.set_page_config(page_title="Stock AI + Nifty Options", layout="centered")
st.title("📈 Stock AI with Nifty 50 Call/Put Indicators")

# — Stock Input & Analysis —
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

if ticker:
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if df.empty or 'Close' not in df.columns:
        st.error("⚠️ Could not fetch stock data. Check ticker.")
    else:
        df['SMA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(14).mean()
        avg_loss = pd.Series(loss).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + avg_gain / avg_loss))

        latest = df.dropna().iloc[-1]
        price, sma, rsi = latest['Close'], latest['SMA20'], latest['RSI']
        st.subheader("📊 Technical Data")
        st.write(f"**Price:** ₹{price:.2f}")
        st.write(f"**SMA‑20:** ₹{sma:.2f}")
        st.write(f"**RSI (14‑day):** {rsi:.2f}")

        signal = "⚪ Hold"
        if price > sma and rsi < 70: signal = "🟢 Buy"
        elif price < sma and rsi > 30: signal = "🔴 Sell"
        st.subheader("🧠 AI Signal")
        st.markdown(signal)
        st.line_chart(df[['Close', 'SMA20']])

# — Nifty Options Chain Fetch Function —
@st.cache_data(ttl=3600)
def get_nifty_chain():
    headers = {
        "User-Agent":"Mozilla/5.0",
        "Accept-Language":"en-US,en;q=0.9",
        "Referer":"https://www.nseindia.com"
    }
    sess = requests.Session()
    sess.headers.update(headers)
    sess.get("https://www.nseindia.com", timeout=5)
    time.sleep(1)
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    res = sess.get(url, headers=headers, timeout=5)
    return res

st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators")

res = get_nifty_chain()
st.write(f"📡 HTTP Status: {res.status_code}")

try:
    data = res.json()
    rows = data['records']['data']
    ce = [r for r in rows if 'CE' in r]
    pe = [r for r in rows if 'PE' in r]

    top_ce = sorted(ce, key=lambda r: r['CE']['openInterest'], reverse=True)[:3]
    top_pe = sorted(pe, key=lambda r: r['PE']['openInterest'], reverse=True)[:3]

    total_ce = sum(r['CE']['openInterest'] for r in ce)
    total_pe = sum(r['PE']['openInterest'] for r in pe)
    pcr = total_pe/total_ce if total_ce else None

    st.write(f"🔁 PCR (Put/Call Ratio): **{pcr:.2f}**")
    st.write(f"🔴 Total Call OI: {total_ce:,}")
    st.write(f"🟢 Total Put OI: {total_pe:,}")

    st.markdown("### 🔴 Top 3 Call OI (Resistance)")
    for r in top_ce:
        st.write(f"₹{r['CE']['strikePrice']} → {r['CE']['openInterest']:,}")

    st.markdown("### 🟢 Top 3 Put OI (Support)")
    for r in top_pe:
        st.write(f"₹{r['PE']['strikePrice']} → {r['PE']['openInterest']:,}")

except Exception as e:
    st.error("❌ Nifty options fetch failed:")
    st.write(res.text[:200])
    st.write(str(e))
