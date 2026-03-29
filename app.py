import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor

# ==============================
# إعداد الصفحة
# ==============================
st.set_page_config(page_title="Crypto Scanner AI PRO", layout="wide")
st.title("🚀 Smart Crypto Scanner AI PRO MAX")

# ==============================
# جلب بيانات السوق
# ==============================
exchange = ccxt.binance()

def get_ohlcv(symbol, timeframe='1h', limit=200):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except:
        return None

# ==============================
# المؤشرات الفنية (بدون pandas_ta)
# ==============================

def rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def ma(df, period=50):
    df[f'ma_{period}'] = df['close'].rolling(period).mean()
    return df

def macd(df):
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    return df

def stoch_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    min_rsi = rsi.rolling(period).min()
    max_rsi = rsi.rolling(period).max()

    df['stoch_rsi'] = (rsi - min_rsi) / (max_rsi - min_rsi)
    return df

# ==============================
# تحليل العملة
# ==============================
def analyze(symbol):
    df = get_ohlcv(symbol)
    if df is None or len(df) < 50:
        return None

    df = rsi(df)
    df = ma(df, 50)
    df = macd(df)
    df = stoch_rsi(df)

    last = df.iloc[-1]

    signal = "HOLD"

    if last['rsi'] < 30 and last['macd'] > last['signal']:
        signal = "BUY 🔥"
    elif last['rsi'] > 70:
        signal = "SELL ⚠️"

    return {
        "symbol": symbol,
        "price": last['close'],
        "rsi": last['rsi'],
        "macd": last['macd'],
        "signal_line": last['signal'],
        "stoch_rsi": last['stoch_rsi'],
        "decision": signal
    }

# ==============================
# جلب العملات (Top USDT)
# ==============================
def get_symbols():
    markets = exchange.load_markets()
    symbols = [s for s in markets if s.endswith('/USDT')]
    return symbols[:50]  # توب 50 بس عشان السرعة

# ==============================
# تشغيل السكينر
# ==============================
if st.button("🚀 Start Scan"):
    symbols = get_symbols()
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        output = executor.map(analyze, symbols)

    for r in output:
        if r:
            results.append(r)

    df = pd.DataFrame(results)
    st.dataframe(df)

    st.success("Done ✅")
