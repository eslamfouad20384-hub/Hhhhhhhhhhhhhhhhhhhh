import pandas as pd
import numpy as np

# =========================
# 1️⃣ تنظيف البيانات
# =========================
def clean_binance_data(raw_data):
    cols = [
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tb_base","tb_quote","ignore"
    ]

    df = pd.DataFrame(raw_data, columns=cols)

    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df.dropna(inplace=True)
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


# =========================
# 2️⃣ RSI
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


# =========================
# 3️⃣ MACD
# =========================
def macd(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal
    return macd_line, signal, hist


# =========================
# 4️⃣ تحليل سكالبينج برو
# =========================
def scalping_analyze(df):
    close = df["close"]
    high = df["high"]
    low = df["low"]

    price = close.iloc[-1]

    # Indicators
    df["rsi"] = rsi(close)
    macd_line, macd_signal, macd_hist = macd(close)

    rsi_val = df["rsi"].iloc[-1]
    macd_val = macd_line.iloc[-1]
    macd_sig = macd_signal.iloc[-1]

    # Trend EMA
    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]

    trend = "UP" if ema20 > ema50 else "DOWN"

    # Support / Resistance (ديناميكي سكالبينج)
    support = low.tail(20).min()
    resistance = high.tail(20).max()

    # Volatility
    atr = (high - low).rolling(14).mean().iloc[-1]

    # =========================
    # 5️⃣ SCORE SYSTEM
    # =========================
    score = 50

    # RSI rules
    if rsi_val < 30:
        score += 20
    elif rsi_val > 70:
        score -= 20

    # MACD rules
    if macd_val > macd_sig:
        score += 15
    else:
        score -= 15

    # Trend rules
    if trend == "UP":
        score += 15
    else:
        score -= 15

    # Position rules
    if price <= support * 1.01:
        score += 10
    if price >= resistance * 0.99:
        score -= 10

    # clamp
    score = max(0, min(100, score))

    # =========================
    # 6️⃣ Signal
    # =========================
    if score >= 75:
        signal = "BUY 🚀 (Scalp Long)"
    elif score <= 35:
        signal = "SELL 🔻 (Scalp Short)"
    else:
        signal = "WAIT ⏳"

    # Targets
    target1 = price + atr
    target2 = price + (atr * 2)
    stop_loss = price - atr

    return {
        "price": price,
        "support": support,
        "resistance": resistance,
        "rsi": rsi_val,
        "macd": macd_val,
        "trend": trend,
        "score": score,
        "signal": signal,
        "target1": target1,
        "target2": target2,
        "stop_loss": stop_loss
    }
