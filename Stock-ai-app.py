import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import traceback
import requests

# -------------------------------------
# 🔷 Page Settings
# -------------------------------------
st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

# -------------------------------------
# 🔷 Stock Analysis
# -------------------------------------
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

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

# -------------------------------------
# 🔷 Nifty 50 Options Indicators
# -------------------------------------
st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators (Options Data)")

try:
    url = "https://niftyapi.vercel.app/api/nifty_option_chain"
    response = requests.get(url, timeout=10)
    result = response.json()

    option_data = result["data"]
    expiry = result["expiry"]

    top_calls = sorted(option_data["calls"], key=lambda x: x["oi"], reverse=True)[:3]
    top_puts = sorted(option_data["puts"], key=lambda x: x["oi"], reverse=True)[:3]

    total_call_oi = sum(item["oi"] for item in option_data["calls"])
    total_put_oi = sum(item["oi"] for item in option_data["puts"])
    pcr = total_put_oi / total_call_oi if total_call_oi else 0

    st.write(f"📅 **Expiry Date:** `{expiry}`")
    st.write(f"🟣 **Put/Call Ratio (PCR):** `{pcr:.2f}`")
    st.write(f"🟢 **Total Put OI:** `{total_put_oi:,}`")
    st.write(f"🔴 **Total Call OI:** `{total_call_oi:,}`")

    st.markdown("### 🛡️ Top 3 Support (Put OI):")
    for row in top_puts:
        st.write(f"- Strike ₹{row['strike']} → OI: {row['oi']:,}")

    st.markdown("### 🔥 Top 3 Resistance (Call OI):")
    for row in top_calls:
        st.write(f"- Strike ₹{row['strike']} → OI: {row['oi']:,}")

    max_pain = 0
    for put in top_puts:
        for call in top_calls:
            if put["strike"] == call["strike"]:
                max_pain = put["strike"]
    st.success(f"🎯 Estimated Max Pain Level: ₹{max_pain}")

except Exception as e:
    st.error("❌ Failed to load Nifty 50 options data.")
    st.code(str(e))
    st.code(traceback.format_exc())
