import streamlit as st
import requests
import pandas as pd
import pandas_ta as ta

st.set_page_config(layout="wide")
st.title("🚀 Crypto Swing Scanner PRO")

# ==============================
# جلب Top 100 من CoinGecko
# ==============================
@st.cache_data(ttl=300)
def get_top_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1
    }
    data = requests.get(url, params=params).json()

    coins = []
    for coin in data:
        symbol = coin["symbol"].upper() + "-USDT"
        coins.append(symbol)

    return coins

# ==============================
# جلب بيانات الشموع من KuCoin
# ==============================
def get_ohlc(symbol):
    url = "https://api.kucoin.com/api/v1/market/candles"
    params = {
        "type": "1hour",
        "symbol": symbol
    }

    res = requests.get(url, params=params).json()

    if "data" not in res:
        return None

    df = pd.DataFrame(res["data"], columns=[
        "time","open","close","high","low","volume","turnover"
    ])

    df = df.astype(float)
    df = df.iloc[::-1].reset_index(drop=True)

    return df

# ==============================
# التحليل
# ==============================
def analyze(df):
    score = 0
    reasons = []

    # Indicators
    df["rsi"] = ta.rsi(df["close"], length=14)

    stoch = ta.stoch(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch["STOCHk_14_3_3"]
    df["stoch_d"] = stoch["STOCHd_14_3_3"]

    macd = ta.macd(df["close"])
    df["macd"] = macd["MACD_12_26_9"]
    df["signal"] = macd["MACDs_12_26_9"]

    bb = ta.bbands(df["close"])
    df["bb_low"] = bb["BBL_20_2.0"]
    df["bb_mid"] = bb["BBM_20_2.0"]

    df["ma100"] = ta.sma(df["close"], length=100)
    df["ma200"] = ta.sma(df["close"], length=200)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # ==============================
    # RSI
    # ==============================
    if last["rsi"] < 30:
        score += 2
        reasons.append("RSI Oversold")

    if prev["rsi"] < 30 and last["rsi"] > prev["rsi"]:
        score += 3
        reasons.append("RSI Bounce")

    # ==============================
    # Stochastic
    # ==============================
    if last["stoch_k"] < 20:
        score += 1

    if prev["stoch_k"] < prev["stoch_d"] and last["stoch_k"] > last["stoch_d"]:
        score += 2
        reasons.append("Stoch Cross Up")

    # ==============================
    # MACD
    # ==============================
    if prev["macd"] < prev["signal"] and last["macd"] > last["signal"]:
        score += 3
        reasons.append("MACD Bullish Cross")

    # ==============================
    # Bollinger Bands
    # ==============================
    if last["close"] < last["bb_low"]:
        score += 2
        reasons.append("Below BB Lower")

    if prev["close"] < prev["bb_low"] and last["close"] > last["bb_low"]:
        score += 1
        reasons.append("Re-entry BB")

    # ==============================
    # Volume
    # ==============================
    vol_avg = df["volume"].rolling(20).mean().iloc[-1]

    if last["volume"] > vol_avg * 1.5:
        score += 3
        reasons.append("High Volume")

    # ==============================
    # Trend (MA100 / MA200)
    # ==============================
    if last["close"] > last["ma200"]:
        trend = "🔥 Uptrend"
        score += 3
    elif last["close"] > last["ma100"]:
        trend = "⚖️ Sideways"
        score += 1
    else:
        trend = "❌ Downtrend"

    # ==============================
    # Signal
    # ==============================
    if score >= 8:
        signal = "🔥 BUY"
    elif score >= 6:
        signal = "👍 GOOD"
    elif score >= 4:
        signal = "👀 WATCH"
    else:
        signal = "❌ SKIP"

    return (
        score,
        signal,
        trend,
        ", ".join(reasons),
        last["close"],
        last["bb_mid"],
        last["low"]
    )

# ==============================
# واجهة البرنامج
# ==============================
if st.button("🔍 Scan Market"):
    coins = get_top_coins()
    results = []

    progress = st.progress(0)
    status = st.empty()

    for i, coin in enumerate(coins):
        status.text(f"Scanning: {coin}")
        progress.progress((i + 1) / len(coins))

        try:
            df = get_ohlc(coin)

            if df is None or len(df) < 210:
                continue

            score, signal, trend, reasons, price, target, stop = analyze(df)

            results.append({
                "Coin": coin,
                "Price": round(price, 4),
                "Score": score,
                "Signal": signal,
                "Trend": trend,
                "Target": round(target, 4),
                "Stop Loss": round(stop, 4),
                "Reason": reasons
            })

        except:
            continue

    if results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values(by="Score", ascending=False)

        st.success("✅ Scan Complete")
        st.dataframe(df_results, use_container_width=True)
    else:
        st.warning("⚠️ No Data Found")
