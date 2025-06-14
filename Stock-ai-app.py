import yfinance as yf
import pandas as pd
import ta
import streamlit as st

st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

ticker = st.text_input("Enter stock ticker (e.g., TCS.NS)", "RELIANCE.NS")

if ticker:
    df = yf.download(ticker, period="6mo", interval="1d")

    if df.empty:
        st.error("⚠️ Could not fetch stock data. Please check the symbol.")
    else:
        # Drop rows with NaN to avoid ValueError from indicators
        df.dropna(inplace=True)

        if df.shape[0] < 20:
            st.warning("⚠️ Not enough data to calculate indicators.")
        else:
            try:
                # Calculate indicators
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                rsi = ta.momentum.RSIIndicator(close=df['Close'], window=14)
                df['RSI'] = rsi.rsi()

                # Again drop NaN after indicators
                df.dropna(inplace=True)

                latest_close = df['Close'].iloc[-1]
                latest_sma = df['SMA20'].iloc[-1]
                latest_rsi = df['RSI'].iloc[-1]

                st.subheader("📊 Latest Technical Data")
                st.write(f"**Current Price:** ₹{latest_close:.2f}")
                st.write(f"**SMA-20:** ₹{latest_sma:.2f}")
                st.write(f"**RSI (14-day):** {latest_rsi:.2f}")

                # Suggestion Logic
                if latest_close > latest_sma and latest_rsi < 70:
                    suggestion = "🟢 **Buy Signal** – Price is above SMA and RSI is healthy."
                elif latest_close < latest_sma and latest_rsi > 30:
                    suggestion = "🔴 **Sell Signal** – Price is below SMA and RSI shows weakness."
                else:
                    suggestion = "⚠️ **Hold** – No clear signal."

                st.subheader("🧠 AI Suggestion")
                st.markdown(suggestion)

                st.line_chart(df[['Close', 'SMA20']])

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
