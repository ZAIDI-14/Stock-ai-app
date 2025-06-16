import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# Setup Streamlit App
st.set_page_config(page_title="Stock AI + Nifty Call/Put", layout="centered")
st.title("📈 Stock AI + Live Nifty Call/Put Indicators")

# Stock Ticker Input
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

if ticker:
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)

    if df.empty or 'Close' not in df.columns:
        st.error("⚠️ Could not fetch stock data.")
    else:
        df = df[['Close']].dropna()

        if len(df) >= 30:
            # Moving Average
            df['SMA20'] = df['Close'].rolling(window=20).mean()

            # RSI Calculation
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()

            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            df.dropna(inplace=True)

            # Get latest row
            latest = df.iloc[-1]

            st.subheader("📊 Latest Technical Data")
            st.write(f"**Price:** ₹{latest['Close']:.2f}")
            st.write(f"**SMA‑20:** ₹{latest['SMA20']:.2f}")
            st.write(f"**RSI:** {latest['RSI']:.2f}")

            # Simple Buy/Sell Signal
            signal = "⚪ Hold"
            if latest['Close'] > latest['SMA20'] and latest['RSI'] < 70:
                signal = "🟢 Buy"
            elif latest['Close'] < latest['SMA20'] and latest['RSI'] > 30:
                signal = "🔴 Sell"

            st.subheader("🧠 Signal")
            st.markdown(signal)

            # Chart
            st.line_chart(df[['Close', 'SMA20']])

        else:
            st.warning("⚠️ Not enough data for indicators. Minimum 30 days required.")

# Live Nifty Option Chain Section
st.markdown("---")
st.subheader("📈 Live Nifty Call/Put Indicators (NSE)")

def get_nifty_chain():
    url = "https://niftyapi.vercel.app/api/nifty_option_chain"
    try:
        return requests.get(url, timeout=10).json()
    except:
        return None

options = get_nifty_chain()

if options and "data" in options:
    calls = options["data"].get("calls", [])
    puts = options["data"].get("puts", [])
    total_call = sum(x.get("oi", 0) for x in calls)
    total_put = sum(x.get("oi", 0) for x in puts)
    pcr = total_put / total_call if total_call else 0

    st.write(f"📊 PCR: **{pcr:.2f}**")
    st.write(f"🔴 Total Call OI: {total_call:,}")
    st.write(f"🟢 Total Put OI: {total_put:,}")

    st.markdown("### 🔴 Top 3 Resistance (Call OI)")
    for x in sorted(calls, key=lambda x: x.get("oi", 0), reverse=True)[:3]:
        st.write(f"₹{x.get('strike')} → {x.get('oi', 0):,}")

    st.markdown("### 🟢 Top 3 Support (Put OI)")
    for x in sorted(puts, key=lambda x: x.get("oi", 0), reverse=True)[:3]:
        st.write(f"₹{x.get('strike')} → {x.get('oi', 0):,}")
else:
    st.error("❌ Failed to load Nifty options data.")
