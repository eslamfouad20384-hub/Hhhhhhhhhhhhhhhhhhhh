import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import requests

# إعداد واجهة Streamlit
st.set_page_config(page_title="Crypto Buy Signal Bot", layout="wide")
st.title("🚀 محرك توصيات الكريبتو الذكي")

# الدالة لجلب بيانات السعر والمؤشرات
def get_data(symbol):
    exchange = ccxt.binance()
    bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
    df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    
    # حساب المؤشرات الفنية
    df['RSI'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    df = pd.concat([df, macd], axis=1)
    return df

# الدالة لجلب الأخبار (مثال باستخدام CryptoPanic API)
def get_sentiment(symbol):
    # ملاحظة: ستحتاج لمفتاح API من cryptopanic.com
    api_key = "YOUR_API_KEY" 
    url = f"https://cryptopanic.com{api_key}&currencies={symbol.split('/')[0]}"
    # تبسيط: هنا يمكنك تحليل النصوص لمعرفة الإيجابية (Sentiment Analysis)
    return "Positive" # قيمة افتراضية للتوضيح

# واجهة المستخدم
symbol = st.sidebar.text_input("أدخل رمز العملة (مثلاً BTC/USDT)", value="BTC/USDT")

if st.button("تحليل السوق"):
    data = get_data(symbol)
    last_row = data.iloc[-1]
    sentiment = get_sentiment(symbol)
    
    # منطق التوصية (Buy Logic)
    # شراء إذا كان RSI أقل من 30 (Oversold) والماكد إيجابي والأخبار جيدة
    is_bullish_macd = last_row['MACDh_12_26_9'] > 0
    is_low_rsi = last_row['RSI'] < 40 
    
    st.subheader(f"تحليل عملة {symbol}")
    col1, col2, col3 = st.columns(3)
    col1.metric("السعر الحالي", f"${last_row['close']}")
    col2.metric("مؤشر RSI", f"{last_row['RSI']:.2f}")
    col3.metric("حالة الأخبار", sentiment)

    if (is_low_rsi or is_bullish_macd) and sentiment == "Positive":
        st.success("✅ توصية: شراء (إشارات إيجابية مجتمعة)")
    else:
        st.warning("⏳ توصية: انتظر (الإشارات غير مكتملة)")
    
    st.line_chart(data['close'])
