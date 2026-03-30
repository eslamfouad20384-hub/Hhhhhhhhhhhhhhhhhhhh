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
# 🌍 Proxy Rotation (اختياري)
# =========================
PROXIES = [
    None,  # بدون بروكسي (أساسي)
    # لو عندك proxies ضيفها هنا:
    # "http://user:pass@ip:port",
    # "http://ip:port",
]

def get_proxy():
    proxy = random.choice(PROXIES)
    if proxy:
        return {"http": proxy, "https": proxy}
    return None


# =========================
# 🚀 Binance Primary API
# =========================
def fetch_binance(session):
    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
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
# 🔄 Fallback API (Coinbase)
# =========================
def fetch_coinbase():
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"

    params = {
        "granularity": 3600
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        if isinstance(data, list):
            return data

        return None

    except:
        return None


# =========================
# 📊 Unified Data Loader
# =========================
def get_data():
    session = create_session()

    # 1️⃣ Binance
    data = fetch_binance(session)

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

    # 2️⃣ Fallback Coinbase
    data = fetch_coinbase()

    if data:
        df = pd.DataFrame(data, columns=[
            "time","low","high","open","close","volume"
        ])

        df["time"] = pd.to_datetime(df["time"], unit="s")

        return df

    # 3️⃣ Fail safe
    return pd.DataFrame()
