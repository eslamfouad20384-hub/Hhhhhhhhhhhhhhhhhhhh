import streamlit as st
import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor

# ==============================
# UI
# ==============================
st.set_page_config(page_title="Swing Crypto Scanner", layout="wide")
st.title("🚀 Swing Trading Crypto Scanner")

# ==============================
# Data
# ==============================
def get_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 30}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        prices = data["prices"]
        df = pd.DataFrame(prices, columns=["time", "close"])
        df["close"] = df["close"].astype(float)

        return df
    except:
        return None

# ==============================
# RSI + Divergence
# ==============================
def rsi_and_divergence(df, period=14):
    delta = df["close"].diff()

    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # نحط نافذة صغيرة للتحليل
    window = df.tail(10)

    # Simple divergence logic
    price_start = window["close"].iloc[0]
    price_end = window["close"].iloc[-1]

    rsi_start = window["rsi"].iloc[0]
    rsi_end = window["rsi"].iloc[-1]

    bullish_div = (price_end < price_start) and (rsi_end > rsi_start)
    bearish_div = (price_end > price_start) and (rsi_end < rsi_start)

    return df, bullish_div, bearish_div

# ==============================
# Indicators
# ==============================
def ma(df, period):
    df[f"ma{period}"] = df["close"].rolling(period).mean()
    return df

def macd(df):
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["macd"] = ema12 - ema26
    df["signal"] = df["macd"].ewm(span=9).mean()
    return df

def bollinger(df):
    df["bb_mid"] = df["close"].rolling(20).mean()
    std = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * std
    df["bb_lower"] = df["bb_mid"] - 2 * std
    return df

# ==============================
# Swing Logic
# ==============================
def analyze_coin(coin):
    df = get_data(coin)
    if df is None or len(df) < 60:
        return None

    df, bullish_div, bearish_div = rsi_and_divergence(df)

    df = ma(df, 50)
    df = ma(df, 200)
    df = macd(df)
    df = bollinger(df)

    last = df.iloc[-1]

    price = last["close"]
    ma50 = last["ma50"]
    ma200 = last["ma200"]

    uptrend = ma50 > ma200

    oversold_pullback = last["rsi"] < 45
    macd_turn = last["macd"] > last["signal"]
    price_reclaim = price > ma50

    swing_buy = uptrend and oversold_pullback and macd_turn and price_reclaim

    signal = "HOLD"

    score = 0
    score += 1 if uptrend else 0
    score += 1 if macd_turn else 0
    score += 1 if oversold_pullback else 0
    score += 1 if price_reclaim else 0

    # 🔥 RSI Divergence Boost
    if bullish_div:
        score += 2

    if swing_buy:
        signal = "SWING BUY 🔥"

    if bullish_div and uptrend:
        signal = "STRONG SWING BUY 🔥🔥"

    target1 = ma50
    target2 = last["bb_mid"]
    target3 = last["bb_upper"]

    stop_loss = ma200

    return {
        "coin": coin,
        "price": price,
        "rsi": last["rsi"],
        "trend": "UP" if uptrend else "DOWN",
        "signal": signal,
        "score": score,
        "bullish_div": bullish_div,
        "bearish_div": bearish_div,
        "target1": target1,
        "target2": target2,
        "target3": target3,
        "stop_loss": stop_loss
    }

# ==============================
# TOP 100 COINS
# ==============================
def get_symbols():
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False
    }

    r = requests.get(url, timeout=10, params=params)
    data = r.json()

    return [coin["id"] for coin in data]

# ==============================
# Run
# ==============================
if st.button("🚀 Start Swing Scan"):
    coins = get_symbols()
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        output = executor.map(analyze_coin, coins)

    for r in output:
        if r:
            results.append(r)

    df = pd.DataFrame(results)

    if not df.empty:
        df = df.sort_values("score", ascending=False)
        st.dataframe(df)
    else:
        st.warning("No data")

    st.success("Done ✅")
