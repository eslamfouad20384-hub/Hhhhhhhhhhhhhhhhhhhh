import requests
import pandas as pd
import numpy as np
import time

# ==============================
# إعدادات
# ==============================
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/v2/histohour"

TOP_COINS = 100

# ==============================
# 1️⃣ جلب أفضل 100 عملة
# ==============================
def get_top_coins():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": TOP_COINS,
        "page": 1
    }
    data = requests.get(COINGECKO_URL, params=params).json()
    return [coin["symbol"].upper() for coin in data]

# ==============================
# 2️⃣ جلب بيانات السعر
# ==============================
def get_price_data(symbol):
    params = {
        "fsym": symbol,
        "tsym": "USDT",
        "limit": 100
    }
    res = requests.get(CRYPTOCOMPARE_URL, params=params).json()

    if "Data" not in res:
        return None

    df = pd.DataFrame(res["Data"]["Data"])
    return df

# ==============================
# 3️⃣ حساب RSI
# ==============================
def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# ==============================
# 4️⃣ حساب MACD
# ==============================
def calculate_macd(df):
    df["EMA12"] = df["close"].ewm(span=12).mean()
    df["EMA26"] = df["close"].ewm(span=26).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    return df

# ==============================
# 5️⃣ حساب المتوسطات
# ==============================
def calculate_ma(df):
    df["MA100"] = df["close"].rolling(100).mean()
    df["MA200"] = df["close"].rolling(200).mean()
    return df

# ==============================
# 6️⃣ Volume Spike
# ==============================
def volume_spike(df):
    avg_vol = df["volumeto"].rolling(20).mean()
    return df["volumeto"].iloc[-1] > avg_vol.iloc[-1] * 1.5

# ==============================
# 7️⃣ RSI Divergence بسيط
# ==============================
def rsi_divergence(df):
    if len(df) < 20:
        return False
    price_low1 = df["close"].iloc[-5]
    price_low2 = df["close"].iloc[-1]
    rsi_low1 = df["RSI"].iloc[-5]
    rsi_low2 = df["RSI"].iloc[-1]

    return price_low2 < price_low1 and rsi_low2 > rsi_low1

# ==============================
# 8️⃣ تحليل العملة
# ==============================
def analyze_coin(symbol):
    df = get_price_data(symbol)
    if df is None or len(df) < 50:
        return None

    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_ma(df)

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

    # Volume
    if volume_spike(df):
        score += 2
        reasons.append("Volume Spike")

    # MA
    price = df["close"].iloc[-1]
    if price > df["MA100"].iloc[-1]:
        score += 1
        reasons.append("Above MA100")

    # Divergence
    if rsi_divergence(df):
        score += 3
        reasons.append("RSI Divergence")

    # فلترة الهبوط
    change = (df["close"].iloc[-1] - df["close"].iloc[-24]) / df["close"].iloc[-24] * 100

    if change > -5:
        return None

    if score >= 5:
        entry = price
        target = price * 1.05
        stop = price * 0.97

        return {
            "symbol": symbol,
            "score": score,
            "entry": entry,
            "target": target,
            "stop": stop,
            "reasons": reasons
        }

    return None

# ==============================
# 9️⃣ تشغيل النظام
# ==============================
def run_scanner():
    coins = get_top_coins()
    results = []

    for coin in coins:
        try:
            res = analyze_coin(coin)
            if res:
                results.append(res)
        except:
            continue

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    print("\n🔥 أفضل فرص سوينج:\n")
    for r in results[:10]:
        print(f"💰 {r['symbol']}")
        print(f"Score: {r['score']}")
        print(f"Entry: {r['entry']:.4f}")
        print(f"Target: {r['target']:.4f}")
        print(f"Stop: {r['stop']:.4f}")
        print(f"Reasons: {', '.join(r['reasons'])}")
        print("-" * 30)

# ==============================
# 🔁 تشغيل مستمر
# ==============================
if __name__ == "__main__":
    while True:
        run_scanner()
        time.sleep(300)  # كل 5 دقايق
