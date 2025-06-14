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
            # ✅ Extract 1D Series for Close prices
            close_series = df['Close'].dropna().squeeze()

            # Ensure enough data
            if close_series.shape[0] < 30:
                st.warning("⚠️ Not enough clean data to calculate indicators.")
            else:
                # Create a clean DataFrame from the Series
                df_clean = pd.DataFrame({'Close': close_series})
                df_clean['SMA20'] = df_clean['Close'].rolling(window=20).mean()
                df_clean.dropna(inplace=True)

                # ✅ RSI calculation using proper 1D Series
                rsi_calc = ta.momentum.RSIIndicator(close=df_clean['Close'], window=14)
                df_clean['RSI'] = rsi_calc.rsi()

                # Get last values
                latest_close = df_clean['Close'].iloc[-1]
                latest_sma = df_clean['SMA20'].iloc[-1]
                latest_rsi = df_clean['RSI'].iloc[-1]

                # Display results
                st.subheader("📊 Latest Technical Data")
                st.write(f"**Current Price:** ₹{latest_close:.2f}")
                st.write(f"**SMA-20:** ₹{latest_sma:.2f}")
                st.write(f"**RSI (14-day):** {latest_rsi:.2f}")

                # Buy/Sell/Hold logic
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
