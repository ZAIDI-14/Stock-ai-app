import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import traceback
import requests

# Page setup
st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

# Input for stock ticker
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

# Fetch stock data
if ticker:
    try:
        df = yf.download(ticker, period="6mo", interval="1d")

        if df.empty or 'Close' not in df.columns:
            st.error("⚠️ Could not fetch stock data. Please check the symbol.")
        else:
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

# -------------------------------------------------------------------
# 📈 NIFTY 50 CALL/PUT INDICATORS (Using NSE Official API with headers)
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators (Options Data)")

try:
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/option-chain"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    response = session.get(url, headers=headers)
    data = response.json()

    records = data["records"]
    ce_data = [d for d in records["data"] if "CE" in d]
    pe_data = [d for d in records["data"] if "PE" in d]

    top_calls = sorted(ce_data, key=lambda x: x["CE"]["openInterest"], reverse=True)[:3]
    top_puts = sorted(pe_data, key=lambda x: x["PE"]["openInterest"], reverse=True)[:3]

    total_call_oi = sum(d["CE"]["openInterest"] for d in ce_data)
    total_put_oi = sum(d["PE"]["openInterest"] for d in pe_data)
    pcr = total_put_oi / total_call_oi if total_call_oi else 0

    st.success("✅ NSE Nifty Options Loaded")
    st.write(f"📊 Put/Call Ratio: **{pcr:.2f}**")

    st.markdown("### 🔴 Top 3 Resistance (Call OI)")
    for c in top_calls:
        st.write(f"Strike ₹{c['CE']['strikePrice']}: OI = {c['CE']['openInterest']:,}")

    st.markdown("### 🟢 Top 3 Support (Put OI)")
    for p in top_puts:
        st.write(f"Strike ₹{p['PE']['strikePrice']}: OI = {p['PE']['openInterest']:,}")

except Exception as e:
    st.error("❌ Failed to load Nifty 50 options data.")
    st.code(traceback.format_exc())
