import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import traceback

st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

if ticker:
    try:
        df = yf.download(ticker, period="6mo", interval="1d")

        if df.empty or 'Close' not in df.columns:
            st.error("⚠️ Could not fetch stock data. Please check the symbol.")
        else:
            # Clean and prepare data
            df = df[['Close']].dropna()
            df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
            df = df.dropna()

            if df.shape[0] < 30:
                st.warning("⚠️ Not enough clean data to calculate indicators.")
            else:
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df.dropna(inplace=True)

                close_series = df['Close'].astype(float)
                rsi_calc = ta.momentum.RSIIndicator(close=close_series, window=14)
                df['RSI'] = rsi_calc.rsi()

                # Get last values
                latest_close = float(df['Close'].iloc[-1])
                latest_sma = float(df['SMA20'].iloc[-1])
                latest_rsi = float(df['RSI'].iloc[-1])

                # Show data
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

                st.line_chart(df[['Close', 'SMA20']])

    except Exception as e:
        st.error("❌ App crashed. Here's the full error:")
        st.code(traceback.format_exc())
