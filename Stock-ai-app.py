import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📊 AI Stock Assistant")

symbol = st.text_input("Enter Stock Symbol (e.g., INFY.NS)", value="INFY.NS")
buy_price = st.number_input("Your Buy Price (₹)", min_value=0.0, value=1500.0)
quantity = st.number_input("Quantity Bought", min_value=1, value=10)

if symbol:
    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")
    current_price = stock.history(period="1d")["Close"].iloc[-1]
    total_cost = buy_price * quantity
    current_value = current_price * quantity
    profit_loss = current_value - total_cost
    breakeven = total_cost / quantity

    st.metric("Current Price", f"₹{current_price:.2f}")
    st.metric("Breakeven", f"₹{breakeven:.2f}")
    st.metric("P/L", f"₹{profit_loss:.2f}")

    if profit_loss >= 1500:
        st.success("💰 Target Met: You made ₹1,500+ profit today!")
    elif profit_loss >= 0:
        st.info("✅ You are in profit. Keep tracking.")
    else:
        st.warning("📉 You are in loss. Be careful.")

    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    data["RSI"] = rsi

    st.line_chart(data[["Close", "RSI"]])

    if rsi.iloc[-1] < 30:
        st.success("📈 Suggestion: RSI is low.")
    elif rsi.iloc[-1] > 70:
        st.error("📉 Suggestion: RSI is high.")
    else:
        st.info("ℹ️ RSI is neutral.")
