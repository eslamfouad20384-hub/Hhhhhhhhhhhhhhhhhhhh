import streamlit as st
import pandas as pd
import numpy as np
import requests

# ==========================
# UI
# ==========================
st.set_page_config(layout="wide")
st.title("🚀 Bitcoin Analyzer PRO MAX")

SYMBOL = "BTCUSDT"
INTERVAL = "1h"
LIMIT = 100

# ==========================
# Get Data (Stable)
# ==========================
def get_data():
    try:
        url = "https://api.binance.com/api/v3/klines"

        params = {
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "limit": LIMIT
        }

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        res = requests.get(url, params=params, headers=headers, timeout=10)

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

        df = df.astype(float)

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
# Support / Resistance
# ==========================
def support_resistance(df):
    highs = df["high"]
    lows = df["low"]

    window = 5
    pivots_high = []
    pivots_low = []

    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i-window:i+window]):
            pivots_high.append(highs[i])

        if lows[i] == min(lows[i-window:i+window]):
            pivots_low.append(lows[i])

    def cluster(levels):
        if len(levels) == 0:
            return []

        levels = sorted(levels)
        clusters = [levels[0]]
        temp = [levels[0]]

        for p in levels[1:]:
            if abs(p - np.mean(temp)) / np.mean(temp) < 0.01:
                temp.append(p)
            else:
                clusters.append(np.mean(temp))
                temp = [p]

        clusters.append(np.mean(temp))
        return clusters

    return cluster(pivots_low), cluster(pivots_high)


# ==========================
# Analysis Engine
# ==========================
def analyze(df):

    # 🚨 حماية كاملة
    if df is None or df.empty or len(df) < 20:
        return None

    df["RSI"] = rsi(df)

    price = df["close"].iloc[-1]
    rsi_now = df["RSI"].iloc[-1]

    support, resistance = support_resistance(df)

    nearest_support = max([s for s in support if s < price], default=None)
    nearest_resistance = min([r for r in resistance if r > price], default=None)

    signal = "HOLD"
    reasons = []

    # ==========================
    # إشارات قوية
    # ==========================
    if rsi_now < 30:
        signal = "BUY"
        reasons.append("RSI Oversold")

    if rsi_now > 70:
        signal = "SELL"
        reasons.append("RSI Overbought")

    if nearest_support and price <= nearest_support * 1.01:
        signal = "BUY"
        reasons.append("Near Support Zone")

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
        "Price": round(price, 2),
        "RSI": round(rsi_now, 2),
        "Support": nearest_support,
        "Resistance": nearest_resistance,
        "Target1": target1,
        "Target2": target2,
        "StopLoss": stop_loss,
        "Signal": signal,
        "Reasons": ", ".join(reasons)
    }


# ==========================
# Run
# ==========================
df = get_data()

if df.empty:
    st.error("❌ No data from Binance API")
    st.stop()

if st.button("🔍 Analyze BTC"):
    result = analyze(df)

    if result is None:
        st.warning("⚠️ Not enough data for analysis")
    else:
        st.success("🔥 Analysis Ready")
        st.json(result)
