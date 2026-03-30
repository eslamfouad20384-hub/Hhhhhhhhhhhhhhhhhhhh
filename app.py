import streamlit as st
import requests
import pandas as pd
import numpy as np

# ==============================
# إعداد الصفحة
# ==============================
st.set_page_config(layout="wide")
st.title("🚀 Smart Crypto Scanner (Swing فرص)")

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/v2/histohour"

TOP_COINS = 100

# ==============================
# جلب العملات
# ==============================
def get_top_coins():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": TOP_COINS,
        "page": 1
    }

    try:
        res = requests.get(COINGECKO_URL, params=params, timeout=10)
        data = res.json()

        if not isinstance(data, list):
            st.error("❌ مشكلة في الداتا من CoinGecko")
            return []

        return [coin["symbol"].upper() for coin in data]

    except:
        st.error("❌ فشل تحميل العملات")
        return []

# ==============================
# بيانات السعر
# ==============================
def get_price_data(symbol):
    try:
        params = {
            "fsym": symbol,
            "tsym": "USDT",
            "limit": 100
        }
        res = requests.get(CRYPTOCOMPARE_URL, params=params, timeout=10).json()

        if "Data" not in res:
            return None

        df = pd.DataFrame(res["Data"]["Data"])
        return df
    except:
        return None

# ==============================
# المؤشرات
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
# تحليل
# ==============================
def analyze(symbol):
    df = get_price_data(symbol)
    if df is None or len(df) < 50:
        return None

    df = add_indicators(df)

    score = 0
    reasons = []

    price = df["close"].iloc[-1]

    # RSI
    if df["RSI"].iloc[-1] < 30:
        score += 2
        reasons.append("RSI Oversold")

    # MACD
    if df["MACD"].iloc[-1] > df["Signal"].iloc[-1]:
        score += 2
        reasons.append("MACD Bullish")

    # Volume
    avg_vol = df["volumeto"].rolling(20).mean().iloc[-1]
    if df["volumeto"].iloc[-1] > avg_vol * 1.5:
        score += 2
        reasons.append("Volume Spike")

    # MA
    if price > df["MA100"].iloc[-1]:
        score += 1
        reasons.append("Above MA100")

    # هبوط
    change = (price - df["close"].iloc[-24]) / df["close"].iloc[-24] * 100
    if change > -5:
        return None

    if score >= 4:
        return {
            "Symbol": symbol,
            "Score": score,
            "Entry": round(price, 4),
            "Target": round(price * 1.05, 4),
            "Stop": round(price * 0.97, 4),
            "Reasons": ", ".join(reasons)
        }

    return None

# ==============================
# زرار التشغيل
# ==============================
if st.button("🔍 Scan السوق"):
    with st.spinner("جارى البحث..."):
        coins = get_top_coins()
        results = []

        progress = st.progress(0)

        for i, coin in enumerate(coins):
            res = analyze(coin)
            if res:
                results.append(res)

            progress.progress((i + 1) / len(coins))

        if results:
            df = pd.DataFrame(results)
            df = df.sort_values(by="Score", ascending=False)

            st.success(f"🔥 تم العثور على {len(df)} فرصة")

            st.dataframe(df, use_container_width=True)

        else:
            st.warning("❌ مفيش فرص حالياً")
