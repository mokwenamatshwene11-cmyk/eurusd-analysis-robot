
import streamlit as st
import yfinance as yf
import pandas as pd

# ============================================
# APP SETTINGS
# ============================================

st.set_page_config(
    page_title="EUR/USD Analysis Robot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 EUR/USD Analysis Robot")
st.caption("Analysis only — no automatic trades")

SYMBOL = "EURUSD=X"

# ============================================
# GET EUR/USD DATA
# ============================================

@st.cache_data(ttl=60)
def get_data():

    data = yf.download(
        SYMBOL,
        period="60d",
        interval="1h",
        auto_adjust=False,
        progress=False
    )

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data.dropna()


data = get_data()

if data.empty:
    st.error("❌ Could not get EUR/USD data.")
    st.stop()

# ============================================
# INDICATORS
# ============================================

close = data["Close"].astype(float)

data["EMA_20"] = close.ewm(
    span=20,
    adjust=False
).mean()

data["EMA_50"] = close.ewm(
    span=50,
    adjust=False
).mean()

# RSI
delta = close.diff()

gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

average_gain = gain.ewm(
    alpha=1 / 14,
    adjust=False
).mean()

average_loss = loss.ewm(
    alpha=1 / 14,
    adjust=False
).mean()

rs = average_gain / average_loss

data["RSI"] = 100 - (
    100 / (1 + rs)
)

data = data.dropna()

# ============================================
# LATEST DATA
# ============================================

latest = data.iloc[-1]

price = float(latest["Close"])
ema20 = float(latest["EMA_20"])
ema50 = float(latest["EMA_50"])
rsi = float(latest["RSI"])

# ============================================
# TREND
# ============================================

if ema20 > ema50:
    trend = "BULLISH 🟢"
elif ema20 < ema50:
    trend = "BEARISH 🔴"
else:
    trend = "NEUTRAL ⚪"

# ============================================
# SIGNAL
# ============================================

if ema20 > ema50 and rsi > 50:
    signal = "BUY 🟢"

elif ema20 < ema50 and rsi < 50:
    signal = "SELL 🔴"

else:
    signal = "NO TRADE ⚪"

# ============================================
# DISPLAY PRICE
# ============================================

st.subheader("💱 EUR/USD")

st.metric(
    "Current Price",
    f"{price:.5f}"
)

# ============================================
# SIGNAL
# ============================================

st.subheader("🤖 Robot Signal")

if signal.startswith("BUY"):
    st.success(signal)

elif signal.startswith("SELL"):
    st.error(signal)

else:
    st.warning(signal)

# ============================================
# MARKET ANALYSIS
# ============================================

st.subheader("📊 Market Analysis")

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "EMA 20",
        f"{ema20:.5f}"
    )

    st.metric(
        "RSI",
        f"{rsi:.2f}"
    )

with col2:

    st.metric(
        "EMA 50",
        f"{ema50:.5f}"
    )

    st.metric(
        "Trend",
        trend
    )

# ============================================
# CHART
# ============================================

st.subheader("📈 EUR/USD Chart")

chart_data = data[
    ["Close", "EMA_20", "EMA_50"]
].tail(200)

st.line_chart(chart_data)

# ============================================
# REFRESH
# ============================================

if st.button("🔄 Refresh Analysis"):

    st.cache_data.clear()
    st.rerun()

# ============================================
# WARNING
# ============================================

st.divider()

st.caption(
    "⚠️ Analysis only. "
    "This robot does not place trades."
)