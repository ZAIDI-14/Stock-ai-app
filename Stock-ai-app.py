import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# App title
st.title("📈 Stock AI with Nifty 50 Call/Put Indicators")

# Input
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

# Load data
@st.cache_data
def load_data(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False)
    return df

if ticker:
    df = load_data(ticker)

    if df.empty or 'Close' not in df.columns or df['Close'].isna().sum() > 5 or len(df) < 30:
        st.warning("⚠️ Not enough clean data to calculate indicators.")
    else:
        df = df[['Close']].dropna().copy()
        close = df['Close'].values

        if close.ndim != 1:
            st.error("❌ Close data is not 1D.")
        else:
            # SMA
            df['SMA_14'] = df['Close'].rolling(window=14).mean()

            # RSI calculation
            delta = np.diff(close)
            up = delta.clip(min=0)
            down = -1 * delta.clip(max=0)

            roll_up = pd.Series(up).rolling(14).mean()
            roll_down = pd.Series(down).rolling(14).mean()

            RS = roll_up / roll_down
            RSI = 100.0 - (100.0 / (1.0 + RS))
            df['RSI'] = RSI

            # Plotting
            st.subheader(f"{ticker} Stock Price & Indicators")
            fig, ax = plt.subplots(2, 1, figsize=(10, 6))

            ax[0].plot(df.index, df['Close'], label='Close')
            ax[0].plot(df.index, df['SMA_14'], label='SMA 14')
            ax[0].set_title('Stock Price & SMA')
            ax[0].legend()

            ax[1].plot(df.index, df['RSI'], label='RSI', color='orange')
            ax[1].axhline(70, color='red', linestyle='--')
            ax[1].axhline(30, color='green', linestyle='--')
            ax[1].set_title('Relative Strength Index (RSI)')
            ax[1].legend()

            st.pyplot(fig)

            # Option chain placeholder (mock)
            st.subheader("🔮 Nifty 50 Call/Put Signal (Mock Data)")
            st.info("Call/Put analysis for Nifty 50 would go here. (Live option data needs NSE scraping or API access)")
