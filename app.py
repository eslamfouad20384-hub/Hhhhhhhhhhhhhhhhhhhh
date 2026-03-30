import streamlit as st
import requests
import pandas as pd
import numpy as np

# ==========================
# UI
# ==========================
st.set_page_config(layout="wide")
st.title("🚀 Bitcoin Smart Analyzer PRO")

SYMBOL = "BTCUSDT"
INTERVAL = "1h"
LIMIT = 500

# ==========================
# جلب البيانات من Binance
# ==========================
def get_data():
    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "limit": LIMIT
    }

    data = requests.get(url, params=params).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)

    return df


# ==========================
# Pivot Highs & Lows (قمم وقيعان)
# ==========================
def find_pivots(df, window=5):
    highs = df["high"]
    lows = df["low"]

    pivot_highs = []
    pivot_lows = []

    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i-window:i+window]):
            pivot_highs.append(highs[i])

        if lows[i] == min(lows[i-window:i+window]):
            pivot_lows.append(lows[i])

    return pivot_highs, pivot_lows


# ==========================
# دعم ومقاومة (Clustering)
# ==========================
def get_support_resistance(pivots):
    levels = pd.Series(pivots)

    if len(levels) == 0:
        return []

    # تجميع مستويات قريبة
    levels = levels.sort_values()
    clusters = []

    cluster = [levels.iloc[0]]

    for price in levels[1:]:
        if abs(price - np.mean(cluster)) / np.mean(cluster) < 0.01:
            cluster.append(price)
        else:
            clusters.append(np.mean(cluster))
            cluster = [price]

    clusters.append(np.mean(cluster))

    return sorted(clusters)


# ==========================
# RSI بسيط
# ==========================
def rsi(df, period=14):
    delta = df["close"].diff()

    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ==========================
# تحليل كامل
# ==========================
def analyze(df):
    df["RSI"] = rsi(df)

    price = df["close"].iloc[-1]

    pivot_highs, pivot_lows = find_pivots(df)

    resistance = get_support_resistance(pivot_highs)
    support = get_support_resistance(pivot_lows)

    nearest_support = max([s for s in support if s < price], default=None)
    nearest_resistance = min([r for r in resistance if r > price], default=None)

    rsi_now = df["RSI"].iloc[-1]

    # ==========================
    # توصية
    # ==========================
    signal = "HOLD"
    reasons = []

    if rsi_now < 30 and nearest_support:
        signal = "BUY"
        reasons.append("RSI Oversold + عند دعم قوي")

    if nearest_resistance and price > nearest_resistance:
        signal = "BREAKOUT"
        reasons.append("اختراق مقاومة")

    if rsi_now > 70:
        signal = "SELL / TAKE PROFIT"
        reasons.append("RSI Overbought")

    # ==========================
    # أهداف
    # ==========================
    target1 = nearest_resistance
    target2 = None

    if nearest_resistance:
        target2 = nearest_resistance * 1.03

    stop_loss = nearest_support if nearest_support else price * 0.95

    return {
        "Price": price,
        "RSI": rsi_now,
        "Support": nearest_support,
        "Resistance": nearest_resistance,
        "Target1": target1,
        "Target2": target2,
        "StopLoss": stop_loss,
        "Signal": signal,
        "Reasons": ", ".join(reasons),
        "Support Levels": support[:5],
        "Resistance Levels": resistance[:5]
    }


# ==========================
# تشغيل
# ==========================
if st.button("🔍 Analyze Bitcoin"):
    df = get_data()
    result = analyze(df)

    st.subheader("📊 Current Analysis")

    st.write(result)

    st.subheader("📉 Support Levels")
    st.write(result["Support Levels"])

    st.subheader("📈 Resistance Levels")
    st.write(result["Resistance Levels"])
