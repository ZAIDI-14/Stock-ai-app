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
        # Remove any missing values in Close
        df = df[['Close']].dropna()
        df = df[df['Close'].notnull()]
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df = df.dropna()

        # Recheck again after cleaning
        if df.shape[0] < 30:
            st.warning("⚠️ Not enough clean data to calculate indicators.")
        else:
            try:
                # Calculate indicators
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df = df.dropna()

                # 🛠️ FIXED: Make sure input is a Series, not DataFrame
                close_series = df['Close'].astype(float)
                rsi_calc = ta.momentum.RSIIndicator(close=close_series, window=14)
                df['RSI'] = rsi_calc.rsi()

                latest_close = df['Close'].iloc[-1]
                latest_sma = df['SMA20'].iloc[-1]
                latest_rsi = df['RSI'].iloc[-1]

                st.subheader("📊 Latest Technical Data")
                st.write(f"**Current Price:** ₹{latest_close:.2f}")
                st.write(f"**SMA-20:** ₹{latest_sma:.2f}")
                st.write(f"**RSI (14-day):** {latest_rsi:.2f}")

                # Buy/Sell Logic
                if latest_close > latest_sma and latest_rsi < 70:
                    suggestion = "🟢 **Buy Signal** – Strong momentum."
                elif latest_close < latest_sma and latest_rsi > 30:
                    suggestion = "🔴 **Sell Signal** – Weak price action."
                else:
                    suggestion = "⚠️ **Hold** – Unclear trend."

                st.subheader("🧠 AI Suggestion")
                st.markdown(suggestion)

                st.line_chart(df[['Close', 'SMA20']])

            except Exception as e:
                st.error(f"❌ Processing error: {str(e)}")
