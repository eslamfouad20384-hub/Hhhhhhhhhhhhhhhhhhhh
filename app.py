import streamlit as st
import requests
import pandas as pd
import numpy as np

# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("🚀 Smart Crypto Scanner AI PRO")

# ==============================
# APIs
# ==============================
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/v2/histohour"

TOP_COINS = 100

# ==============================
# Cache Coins
# ==============================
@st.cache_data(ttl=300)
def get_top_coins():
    try:
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": TOP_COINS,
            "page": 1
        }

        res = requests.get(COINGECKO_URL, params=params, timeout=10)
        data = res.json()

        if not isinstance(data, list):
            return []

        return [c["symbol"].upper() for c in data if "symbol" in c]

    except:
        return []

# ==============================
# Price Data
# ==============================
def fetch_crypto_data(symbol):
    try:
        params = {
            "fsym": symbol,
            "tsym": "USDT",
            "limit": 120
        }

        res = requests.get(CRYPTOCOMPARE_URL, params=params, timeout=10)

        try:
            data = res.json()
        except:
            return None

        if not isinstance(data, dict):
            return None

        if "Data" not in data or "Data" not in data["Data"]:
            return None

        df = pd.DataFrame(data["Data"]["Data"])

        if df.empty:
            return None

        return df

    except:
        return None

# ==============================
# Indicators
# ==============================
def add_indicators(df):
    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    df["EMA12"] = df["close"].ewm(span=12).mean()
    df["EMA26"] = df["close"].ewm(span=26).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9).mean()

    # MA Trend
    df["MA100"] = df["close"].rolling(100).mean()

    return df

# ==============================
# RSI Divergence (Real)
# ==============================
def detect_rsi_divergence(df):
    if len(df) < 30:
        return False

    price_low1 = df["close"].iloc[-20:-10].min()
    price_low2 = df["close"].iloc[-10:].min()

    rsi_low1 = df["RSI"].iloc[-20:-10].min()
    rsi_low2 = df["RSI"].iloc[-10:].min()

    # Bullish divergence
    if price_low2 < price_low1 and rsi_low2 > rsi_low1:
        return True

    return False

# ==============================
# AI Analysis Engine
# ==============================
def analyze(symbol):
    df = fetch_crypto_data(symbol)

    if df is None or len(df) < 60:
        return None

    df = add_indicators(df)

    price = df["close"].iloc[-1]

    score = 0
    reasons = []

    # ==========================
    # RSI
    # ==========================
    rsi = df["RSI"].iloc[-1]

    if rsi < 30:
        score += 3
        reasons.append("RSI Oversold")
    elif rsi < 40:
        score += 1
        reasons.append("RSI Weak Zone")

    # ==========================
    # MACD
    # ==========================
    if df["MACD"].iloc[-1] > df["Signal"].iloc[-1]:
        score += 2
        reasons.append("MACD Bullish Cross")

    # ==========================
    # Volume Spike
    # ==========================
    try:
        avg_vol = df["volumeto"].rolling(20).mean().iloc[-1]
        if df["volumeto"].iloc[-1] > avg_vol * 1.5:
            score += 2
            reasons.append("Volume Spike")
    except:
        pass

    # ==========================
    # Trend Filter
    # ==========================
    try:
        if price > df["MA100"].iloc[-1]:
            score += 1
            reasons.append("Above MA100")
    except:
        pass

    # ==========================
    # RSI Divergence (Strong)
    # ==========================
    if detect_rsi_divergence(df):
        score += 4
        reasons.append("🔥 RSI Divergence")

    # ==========================
    # Drop Filter
    # ==========================
    try:
        change = (price - df["close"].iloc[-24]) / df["close"].iloc[-24] * 100
        if change > -5:
            return None
    except:
        return None

    # ==========================
    # Final Decision
    # ==========================
    if score >= 5:
        return {
            "Symbol": symbol,
            "Score": score,
            "Entry": round(price, 6),
            "Target": round(price * 1.06, 6),
            "Stop": round(price * 0.97, 6),
            "Reasons": ", ".join(reasons)
        }

    return None

# ==============================
# Scanner
# ==============================
def run_scan():
    coins = get_top_coins()

    if not coins:
        st.error("❌ Error loading coins")
        return

    results = []
    progress = st.progress(0)

    for i, c in enumerate(coins):
        try:
            res = analyze(c)
            if res:
                results.append(res)
        except:
            pass

        progress.progress((i + 1) / len(coins))

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values("Score", ascending=False)

        st.success(f"🔥 Found {len(df)} opportunities")

        st.dataframe(df, use_container_width=True)
    else:
        st.warning("❌ No strong setups right now")

# ==============================
# Run Button
# ==============================
if st.button("🔍 Scan Market"):
    with st.spinner("Analyzing market..."):
        run_scan()
