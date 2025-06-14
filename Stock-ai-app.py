import yfinance as yf
import pandas as pd
import ta
import streamlit as st
import traceback
import requests

# Page setup
st.set_page_config(page_title="Stock AI", layout="centered")
st.title("📈 Smart Stock Buy/Sell + Nifty Call/Put AI")

# — Stock Analysis —
ticker = st.text_input("Enter stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")
if ticker:
    try:
        df = yf.download(ticker, period="6mo", interval="1d")
        if df.empty or 'Close' not in df.columns:
            st.error("⚠️ Could not fetch stock data.")
        else:
            cs = df['Close'].dropna().squeeze()
            if cs.shape[0] < 30:
                st.warning("⚠️ Not enough data for indicators.")
            else:
                dfc = pd.DataFrame({'Close': cs})
                dfc['SMA20'] = dfc['Close'].rolling(20).mean().dropna()
                rsi = ta.momentum.RSIIndicator(close=dfc['Close'], window=14).rsi()
                dfc['RSI'] = rsi

                price, sma20, rsi_val = dfc.iloc[-1][['Close','SMA20','RSI']]
                st.subheader("📊 Technical Data")
                st.write(f"**Price:** ₹{price:.2f}")
                st.write(f"**SMA‑20:** ₹{sma20:.2f}")
                st.write(f"**RSI (14d):** {rsi_val:.2f}")

                signal = "🟢 **Buy**" if price > sma20 and rsi_val < 70 \
                    else "🔴 **Sell**" if price < sma20 and rsi_val > 30 \
                    else "⚠️ **Hold**"
                st.subheader("🧠 Signal")
                st.markdown(signal)
                st.line_chart(dfc[['Close', 'SMA20']])
    except Exception:
        st.error("❌ Stock analysis failed.")
        st.code(traceback.format_exc())

# — Nifty 50 Options —
st.markdown("---")
st.subheader("📈 Nifty 50 Call/Put Indicators (Options)")

try:
    api_url = "https://niftyapi.vercel.app/api/nifty_option_chain"
    resp = requests.get(api_url, timeout=10)
    resp.raise_for_status()
    data = resp.json()['data']
    expiry = resp.json()['expiry']

    calls = sorted(data['calls'], key=lambda x: x['oi'], reverse=True)[:3]
    puts = sorted(data['puts'], key=lambda x: x['oi'], reverse=True)[:3]
    total_c = sum(item['oi'] for item in data['calls'])
    total_p = sum(item['oi'] for item in data['puts'])
    pcr = total_p / total_c if total_c else 0

    st.write(f"📅 **Expiry:** {expiry}")
    st.write(f"🟣 **Put/Call Ratio:** {pcr:.2f}")
    st.write(f"🔴 **Total Call OI:** {total_c:,}")
    st.write(f"🟢 **Total Put OI:** {total_p:,}")

    st.markdown("### 🔥 Top 3 Resistance (Call OI):")
    for x in calls:
        st.write(f"Strike ₹{x['strike']}: OI = {x['oi']:,}")

    st.markdown("### 🛡️ Top 3 Support (Put OI):")
    for x in puts:
        st.write(f"Strike ₹{x['strike']}: OI = {x['oi']:,}")

    maxpain = next((c['strike'] for c in calls if any(p['strike'] == c['strike'] for p in puts)), None)
    st.success(f"🎯 Max Pain Strike: ₹{maxpain}")

except Exception as e:
    st.error("❌ Nifty options data error.")
    st.code(str(e))
    st.code(traceback.format_exc())
