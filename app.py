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
# Indicators
# ==============================
def rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df

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

    df = rsi(df)
    df = ma(df, 50)
    df = ma(df, 200)
    df = macd(df)
    df = bollinger(df)

    last = df.iloc[-1]

    price = last["close"]
    ma50 = last["ma50"]
    ma200 = last["ma200"]

    # ==========================
    # Trend Filter (Swing مهم جداً)
    # ==========================
    uptrend = ma50 > ma200

    # ==========================
    # Pullback + Reversal
    # ==========================
    oversold_pullback = last["rsi"] < 45
    macd_turn = last["macd"] > last["signal"]
    price_reclaim = price > ma50

    swing_buy = uptrend and oversold_pullback and macd_turn and price_reclaim

    signal = "HOLD"

    if swing_buy:
        signal = "SWING BUY 🔥"

    # ==========================
    # Swing Targets
    # ==========================
    target1 = ma50
    target2 = last["bb_mid"]
    target3 = last["bb_upper"]

    stop_loss = ma200  # حماية قوية

    # ==========================
    # Strength Score
    # ==========================
    score = 0
    score += 1 if uptrend else 0
    score += 1 if macd_turn else 0
    score += 1 if oversold_pullback else 0
    score += 1 if price_reclaim else 0

    return {
        "coin": coin,
        "price": price,
        "rsi": last["rsi"],
        "trend": "UP" if uptrend else "DOWN",
        "signal": signal,
        "score": score,
        "target1": target1,
        "target2": target2,
        "target3": target3,
        "stop_loss": stop_loss
    }

# ==============================
# Coins
# ==============================
def get_symbols():
    return [
        "bitcoin","ethereum","binancecoin","ripple","solana",
        "dogecoin","cardano","chainlink","avalanche-2","matic-network",
        "litecoin","polkadot","tron","near","aptos","arbitrum",
        "optimism","render-token","injective","kaspa","sei-network"
    ]

# ==============================
# Run
# ==============================
if st.button("🚀 Start Swing Scan"):
    coins = get_symbols()
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        output = executor.map(analyze_coin, coins)

    for r in output:
        if r and r["signal"] == "SWING BUY 🔥":
            results.append(r)

    df = pd.DataFrame(results)

    if not df.empty:
        df = df.sort_values("score", ascending=False)
        st.dataframe(df)
    else:
        st.warning("No swing setups right now")

    st.success("Done ✅")
