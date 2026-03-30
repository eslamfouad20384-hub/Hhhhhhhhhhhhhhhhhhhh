import streamlit as st
import requests
import pandas as pd
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# 🌐 Pro Session Setup
# =========================
def create_session():
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


# =========================
# 🌍 Proxy Rotation
# =========================
PROXIES = [
    None,
]

def get_proxy():
    proxy = random.choice(PROXIES)
    if proxy:
        return {"http": proxy, "https": proxy}
    return None


# =========================
# 🚀 Binance API
# =========================
def fetch_binance(session, symbol, interval):
    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 100
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    try:
        res = session.get(
            url,
            params=params,
            headers=headers,
            proxies=get_proxy(),
            timeout=10
        )

        data = res.json()

        if not isinstance(data, list):
            return None

        return data

    except:
        return None


# =========================
# 🔄 Fallback API
# =========================
def fetch_coinbase():
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"

    params = {"granularity": 3600}

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        if isinstance(data, list):
            return data

        return None

    except:
        return None


# =========================
# 📊 Unified Loader
# =========================
def get_data(symbol, interval):
    session = create_session()

    data = fetch_binance(session, symbol, interval)

    if data:
        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "close_time","qav","trades","tb_base","tb_quote","ignore"
        ])

        df = df[["time","open","high","low","close","volume"]]

        for c in ["open","high","low","close","volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df["time"] = pd.to_datetime(df["time"], unit="ms")

        return df

    # fallback (اختياري ثابت BTC فقط)
    data = fetch_coinbase()

    if data:
        df = pd.DataFrame(data, columns=[
            "time","low","high","open","close","volume"
        ])

        df["time"] = pd.to_datetime(df["time"], unit="s")

        return df

    return pd.DataFrame()


# =========================
# 📊 Analysis
# =========================
def analyze(df):
    price = df["close"].iloc[-1]
    support = df["low"].tail(20).min()
    resistance = df["high"].tail(20).max()

    return price, support, resistance


# =========================
# 🚀 UI
# =========================
st.set_page_config(page_title="Crypto Pro Scanner", layout="wide")
st.title("🚀 Crypto Pro Scanner")

symbol = st.text_input("💰 العملة", "BTCUSDT")
interval = st.selectbox("⏱ الفريم", ["1m","5m","15m","1h","4h","1d"])

# زر البحث
if st.button("🔍 بحث وتحليل"):

    df = get_data(symbol, interval)

    if df.empty:
        st.error("❌ No data from API")
        st.stop()

    price, support, resistance = analyze(df)

    st.success("✅ تم التحليل")

    st.write("💰 السعر:", price)
    st.write("🟢 الدعم:", support)
    st.write("🔴 المقاومة:", resistance)

    st.line_chart(df.set_index("time")["close"])
