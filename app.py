import streamlit as st
import requests
import pandas as pd
import numpy as np

# =========================
# 📊 جلب البيانات من Binance
# =========================
def get_data():
    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "limit": 100
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        if not isinstance(data, list):
            print("API Error:", data)
            return pd.DataFrame()

        if len(data) == 0:
            print("Empty data from Binance")
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","quote_asset_volume","trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])

        for col in ["open","high","low","close","volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(inplace=True)

        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df.sort_values("time", inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    except Exception as e:
        print("Request Failed:", str(e))
        return pd.DataFrame()


# =========================
# 📈 Indicators
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()
    return macd_line, signal


# =========================
# 🧠 تحليل سكالبينج برو
# =========================
def analyze(df):
    if df.empty:
        return None

    close = df["close"]
    high = df["high"]
    low = df["low"]

    price = close.iloc[-1]

    # Indicators
    df["rsi"] = rsi(close)
    macd_line, macd_signal = macd(close)

    rsi_val = df["rsi"].iloc[-1]
    macd_val = macd_line.iloc[-1]
    macd_sig = macd_signal.iloc[-1]

    # Trend
    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]

    trend = "UP" if ema20 > ema50 else "DOWN"

    # Support / Resistance
    support = low.tail(20).min()
    resistance = high.tail(20).max()

    # Score system
    score = 50

    if rsi_val < 30:
        score += 20
    elif rsi_val > 70:
        score -= 20

    if macd_val > macd_sig:
        score += 15
    else:
        score -= 15

    if trend == "UP":
        score += 15
    else:
        score -= 15

    score = max(0, min(100, score))

    # Signal
    if score >= 75:
        signal = "BUY 🚀"
    elif score <= 35:
        signal = "SELL 🔻"
    else:
        signal = "WAIT ⏳"

    # Targets
    atr = (high - low).rolling(14).mean().iloc[-1]

    return {
        "price": price,
        "rsi": rsi_val,
        "trend": trend,
        "support": support,
        "resistance": resistance,
        "score": score,
        "signal": signal,
        "target1": price + atr,
        "target2": price + (atr * 2),
        "stop_loss": price - atr
    }


# =========================
# 🚀 Streamlit UI
# =========================
st.set_page_config(page_title="Scalping Bot PRO", layout="wide")
st.title("🚀 Crypto Scalping Bot PRO (Binance)")

if st.button("🔥 Scan BTC"):
    df = get_data()

    if df.empty:
        st.error("❌ No data from Binance API")
        st.stop()

    result = analyze(df)

    if result:
        st.success("✅ Analysis Ready")

        st.write("### 💰 Price:", result["price"])
        st.write("### 📊 RSI:", result["rsi"])
        st.write("### 📈 Trend:", result["trend"])
        st.write("### 🎯 Support:", result["support"])
        st.write("### 🎯 Resistance:", result["resistance"])
        st.write("### 🧠 Score:", result["score"])
        st.write("### 📢 Signal:", result["signal"])

        st.write("### 🎯 Targets")
        st.write("TP1:", result["target1"])
        st.write("TP2:", result["target2"])
        st.write("SL:", result["stop_loss"])
