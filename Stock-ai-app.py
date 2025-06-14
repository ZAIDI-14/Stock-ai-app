import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import traceback
import requests

st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

if ticker:
    try:
        df = yf.download(ticker, period="6mo", interval="1d")

        if df.empty or 'Close' not in df.columns:
            st.error("⚠️ Could not fetch stock data. Please check the symbol.")
        else:
            # ✅ Clean Close prices
            close_series = df['Close'].dropna().squeeze()

            if close_series.shape[0] < 30:
                st.warning("⚠️ Not enough clean data to calculate indicators.")
            else:
                df_clean = pd.DataFrame({'Close': close_series})
                df_clean['SMA20'] = df_clean['Close'].rolling(window=20).mean()
                df_clean.dropna(inplace=True)

                rsi_calc = ta.momentum.RSIIndicator(close=df_clean['Close'], window=14)
                df_clean['RSI'] = rsi_calc.rsi()

                latest_close = df_clean['Close'].iloc[-1]
                latest_sma = df_clean['SMA20'].iloc[-1]
                latest_rsi = df_clean['RSI'].iloc[-1]

                st.subheader("📊 Latest Technical Data")
                st.write(f"**Current Price:** ₹{latest_close:.2f}")
                st.write(f"**SMA-20:** ₹{latest_sma:.2f}")
                st.write(f"**RSI (14-day):** {latest_rsi:.2f}")

                if latest_close > latest_sma and latest_rsi < 70:
                    suggestion = "🟢 **Buy Signal** – Strong momentum."
                elif latest_close < latest_sma and latest_rsi > 30:
                    suggestion = "🔴 **Sell Signal** – Weak price action."
                else:
                    suggestion = "⚠️ **Hold** – Unclear trend."

                st.subheader("🧠 AI Suggestion")
                st.markdown(suggestion)

                st.line_chart(df_clean[['Close', 'SMA20']])

    except Exception as e:
        st.error("❌ App crashed. Here's the full error:")
        st.code(traceback.format_exc())

# -----------------------------------
# 🧠 NIFTY 50 OPTIONS INDICATORS
# -----------------------------------

st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators (Options Data)")

try:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    session = requests.Session()
    session.headers.update(headers)

    # NSE requires visiting homepage first
    session.get("https://www.nseindia.com", timeout=5)
    response = session.get(url, timeout=5)
    data = response.json()

    records = data['records']
    all_data = records['data']
    expiry = records['expiryDates'][0]

    call_oi_total = 0
    put_oi_total = 0
    max_pain = 0
    top_calls = []
    top_puts = []

    for row in all_data:
        strike = row.get("strikePrice")
        ce = row.get("CE")
        pe = row.get("PE")

        if ce and ce.get("expiryDate") == expiry:
            call_oi = ce.get("openInterest", 0)
            call_oi_total += call_oi
            top_calls.append((strike, call_oi))

        if pe and pe.get("expiryDate") == expiry:
            put_oi = pe.get("openInterest", 0)
            put_oi_total += put_oi
            top_puts.append((strike, put_oi))

    top_calls = sorted(top_calls, key=lambda x: x[1], reverse=True)[:3]
    top_puts = sorted(top_puts, key=lambda x: x[1], reverse=True)[:3]

    for strike, _ in top_calls:
        for p_strike, _ in top_puts:
            if strike == p_strike:
                max_pain = strike

    pcr = put_oi_total / call_oi_total if call_oi_total else 0

    st.write(f"📅 **Expiry Date:** `{expiry}`")
    st.write(f"🟣 **Put/Call Ratio (PCR):** `{pcr:.2f}`")
    st.write(f"🟢 **Total Put OI:** `{put_oi_total:,}`")
    st.write(f"🔴 **Total Call OI:** `{call_oi_total:,}`")

    st.markdown("### 🛡️ Top 3 Support (Put OI):")
    for strike, oi in top_puts:
        st.write(f"- Strike ₹{strike} → OI: {oi:,}")

    st.markdown("### 🔥 Top 3 Resistance (Call OI):")
    for strike, oi in top_calls:
        st.write(f"- Strike ₹{strike} → OI: {oi:,}")

    st.success(f"🎯 Estimated Max Pain Level: ₹{max_pain}")

except Exception as e:
    st.error("❌ Failed to fetch Nifty 50 options data.")
    st.code(str(e))
    st.code(traceback.format_exc())
