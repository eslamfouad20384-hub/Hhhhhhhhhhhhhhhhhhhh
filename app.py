import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# ==============================
# إعداد الصفحة
# ==============================
st.set_page_config(layout="wide")
st.title("🚀 Smart Crypto Scanner PRO (Stable Version)")

# ==============================
# API Sources
# ==============================
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/v2/histohour"

TOP_COINS = 100

# ==============================
# Cache (مهم جدًا)
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
# جلب البيانات (مع حماية قوية)
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

        if "Data" not in data:
            return None

        if "Data" not in data["Data"]:
            return None

        df = pd.DataFrame(data["Data"]["Data"])

        if df.empty:
            return None

        return df

    except:
        return None

# ==============================
# مؤشرات
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

    # MA
    df["MA100"] = df["close"].rolling(100).mean()

    return df

# ==============================
# تحليل العملة
# ==============================
def analyze(symbol):
    df = fetch_crypto_data(symbol)

    if df is None or not isinstance(df, pd.DataFrame):
        return None

    if len(df) < 60:
        return None

    df = add_indicators(df)

    price = df["close"].iloc[-1]
    score = 0
    reasons = []

    # RSI
    if df["RSI"].iloc[-1] < 30:
        score += 2
        reasons.append("RSI Oversold")

    # MACD
    if df["MACD"].iloc[-1] > df["Signal"].iloc[-1]:
        score += 2
        reasons.append("MACD Bullish")

    # Volume Spike
    try:
        avg_vol = df["volumeto"].rolling(20).mean().iloc[-1]
        if df["volumeto"].iloc[-1] > avg_vol * 1.5:
            score += 2
            reasons.append("Volume Spike")
    except:
        pass

    # MA filter
    if price > df["MA100"].iloc[-1]:
        score += 1
        reasons.append("Above MA100")

    # Drop filter
    try:
        change = (price - df["close"].iloc[-24]) / df["close"].iloc[-24] * 100
        if change > -5:
            return None
    except:
        return None

    if score >= 4:
        return {
            "Symbol": symbol,
            "Score": score,
            "Entry": round(price, 5),
            "Target": round(price * 1.05, 5),
            "Stop": round(price * 0.97, 5),
            "Reasons": ", ".join(reasons)
        }

    return None

# ==============================
# Scanner
# ==============================
def run_scan():
    coins = get_top_coins()

    if not coins:
        st.error("❌ مشكلة في جلب العملات")
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

        st.success(f"🔥 تم العثور على {len(df)} فرصة")

        st.dataframe(df, use_container_width=True)
    else:
        st.warning("❌ مفيش فرص حالياً")

# ==============================
# زر التشغيل
# ==============================
if st.button("🔍 Scan Now"):
    with st.spinner("جارى التحليل..."):
        run_scan()
