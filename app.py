import streamlit as st
import pandas as pd
import numpy as np
import requests

# ==========================
# UI
# ==========================
st.set_page_config(layout="wide")
st.title("🚀 Bitcoin Analyzer PRO (Stable)")

SYMBOL = "BTCUSDT"
INTERVAL = "1h"
LIMIT = 100

# ==========================
# جلب البيانات (Stable API)
# ==========================
def get_data():
    try:
        url = "https://api.binance.com/api/v3/klines"

        params = {
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "limit": LIMIT
        }

        res = requests.get(url, params=params, timeout=10)

        if res.status_code != 200:
            return pd.DataFrame()

        data = res.json()

        if not isinstance(data, list) or len(data) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qav","trades","tbbav","tbqav","ignore"
        ])

        df = df[["open","high","low","close","volume"]]

        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)

        return df

    except:
        return pd.DataFrame()


# ==========================
# RSI
# ==========================
def rsi(df, period=14):
    delta = df["close"].diff()

    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ==========================
# دعم ومقاومة (Pivot)
# ==========================
def find_levels(df):
    highs = df["high"]
    lows = df["low"]

    resistance = []
    support = []

    window = 5

    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i-window:i+window]):
            resistance.append(highs[i])

        if lows[i] == min(lows[i-window:i+window]):
            support.append(lows[i])

    def cluster(levels):
        if len(levels) == 0:
            return []

        levels = sorted(levels)
        clusters = []
        temp = [levels[0]]

        for p in levels[1:]:
            if abs(p - np.mean(temp)) / np.mean(temp) < 0.01:
                temp.append(p)
            else:
                clusters.append(np.mean(temp))
                temp = [p]

        clusters.append(np.mean(temp))
        return clusters

    return cluster(support), cluster(resistance)


# ==========================
# تحليل
# ==========================
def analyze(df):

    # 🚨 حماية من الفشل
    if df is None or df.empty or len(df) < 20:
        return None

    df["RSI"] = rsi(df)

    price = df["close"].iloc[-1]

    support, resistance = find_levels(df)

    nearest_support = max([s for s in support if s < price], default=None)
    nearest_resistance = min([r for r in resistance if r > price], default=None)

    rsi_now = df["RSI"].iloc[-1]

    signal = "HOLD"
    reasons = []

    # ==========================
    # إشارات
    # ==========================
    if rsi_now < 30:
        signal = "BUY"
        reasons.append("RSI Oversold")

    if rsi_now > 70:
        signal = "SELL"
        reasons.append("RSI Overbought")

    if nearest_support and price <= nearest_support * 1.01:
        signal = "BUY"
        reasons.append("Near Support")

    if nearest_resistance and price >= nearest_resistance:
        signal = "BREAKOUT / SELL"
        reasons.append("At Resistance")

    # ==========================
    # أهداف
    # ==========================
    target1 = nearest_resistance
    target2 = nearest_resistance * 1.03 if nearest_resistance else None

    stop_loss = nearest_support * 0.98 if nearest_support else price * 0.95

    return {
        "Price": price,
        "RSI": rsi_now,
        "Support": nearest_support,
        "Resistance": nearest_resistance,
        "Target1": target1,
        "Target2": target2,
        "StopLoss": stop_loss,
        "Signal": signal,
        "Reasons": ", ".join(reasons)
    }


# ==========================
# تشغيل
# ==========================
df = get_data()

if df.empty:
    st.error("❌ No data from Binance API. Try again.")
    st.stop()

if st.button("🔍 Analyze BTC"):
    result = analyze(df)

    if result is None:
        st.warning("⚠️ Not enough data to analyze")
    else:
        st.subheader("📊 Analysis Result")
        st.write(result)
