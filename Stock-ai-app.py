import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import numpy as np
import datetime

# ---------- Page Setup ----------
st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📈 Smart Stock Buy/Sell Suggestion")

# ---------- User Input ----------
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")

# ---------- Fetch Stock Data ----------
@st.cache_data
def get_stock_data(ticker):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=100)
    data = yf.download(ticker, start=start, end=end)
    return data

data = get_stock_data(ticker)

if data.empty:
    st.error("Failed to fetch stock data. Check the ticker symbol.")
    st.stop()

# ---------- Technical Indicators ----------
data['SMA20'] = data['Close'].rolling(window=20).mean()
delta = data['Close'].diff()
gain = np.where(delta > 0, delta, 0)
loss = np.where(delta < 0, -delta, 0)
avg_gain = pd.Series(gain).rolling(window=14).mean()
avg_loss = pd.Series(loss).rolling(window=14).mean()
rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
current_price = round(data['Close'][-1], 2)
sma20 = round(data['SMA20'][-1], 2)
current_rsi = round(rsi.iloc[-1], 2)

# ---------- Display Technicals ----------
st.subheader("📊 Latest Technical Data")
st.markdown(f"**Current Price:** ₹{current_price}")
st.markdown(f"**SMA-20:** ₹{sma20}")
st.markdown(f"**RSI (14-day):** {current_rsi}")

# ---------- Simple AI Suggestion ----------
suggestion = "🟡 **Hold** – Wait for better clarity."
if current_price < sma20 and current_rsi < 40:
    suggestion = "🔴 **Sell Signal** – Weak price action."
elif current_price > sma20 and current_rsi > 60:
    suggestion = "🟢 **Buy Signal** – Bullish trend detected."

st.subheader("🧠 AI Suggestion")
st.markdown(suggestion)

# ---------- Plot Chart ----------
st.line_chart(data[['Close', 'SMA20']])

# ---------- Nifty Options Data ----------
st.subheader("📈 Nifty 50 Call/Put Indicators (Options Data)")

def fetch_nifty_oi_data():
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }
    with requests.Session() as session:
        session.get("https://www.nseindia.com", headers=headers)
        response = session.get(url, headers=headers)
        try:
            data = response.json()
            return data
        except Exception as e:
            st.error(f"❌ Failed to load Nifty 50 options data.\n`{e}`")
            return None

nifty_data = fetch_nifty_oi_data()

if nifty_data:
    records = nifty_data['records']['data']
    ce_oi = []
    pe_oi = []
    strikes = []

    for item in records:
        if 'CE' in item and 'PE' in item:
            ce_oi.append(item['CE']['openInterest'])
            pe_oi.append(item['PE']['openInterest'])
            strikes.append(item['strikePrice'])

    if ce_oi and pe_oi:
        max_ce = max(ce_oi)
        max_pe = max(pe_oi)
        ce_strike = strikes[ce_oi.index(max_ce)]
        pe_strike = strikes[pe_oi.index(max_pe)]

        st.markdown(f"🔵 **Highest Call OI (Resistance):** {ce_strike} with OI {max_ce}")
        st.markdown(f"🟢 **Highest Put OI (Support):** {pe_strike} with OI {max_pe}")

        chart_data = pd.DataFrame({
            'Strike Price': strikes,
            'Call OI': ce_oi,
            'Put OI': pe_oi
        })
        chart_data.set_index('Strike Price', inplace=True)
        st.bar_chart(chart_data)
    else:
        st.warning("No options data found.")
