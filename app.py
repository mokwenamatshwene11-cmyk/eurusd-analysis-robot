import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(
    page_title="EUR/USD Analysis Robot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 EUR/USD Analysis Robot")
st.caption("Analysis only — no automatic trades")

SYMBOL = "EURUSD=X"

# ==============================
# SETTINGS
# ==============================

STOP_DISTANCE = 0.0020
TAKE_DISTANCE = 0.0040


# ==============================
# DOWNLOAD DATA
# ==============================

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


# ==============================
# INDICATORS
# ==============================

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


# ==============================
# RECENT MOMENTUM
# ==============================

data["Price_Change"] = close.pct_change(
    periods=3
) * 100

data = data.dropna()

latest = data.iloc[-1]
previous = data.iloc[-2]

price = float(latest["Close"])
ema20 = float(latest["EMA_20"])
ema50 = float(latest["EMA_50"])
rsi = float(latest["RSI"])
momentum = float(latest["Price_Change"])


# ==============================
# TREND
# ==============================

if ema20 > ema50:
    trend = "BULLISH 🟢"
elif ema20 < ema50:
    trend = "BEARISH 🔴"
else:
    trend = "NEUTRAL ⚪"


# ==============================
# SIGNAL SCORING
# ==============================

buy_score = 0
sell_score = 0


# EMA trend

if ema20 > ema50:
    buy_score += 30

elif ema20 < ema50:
    sell_score += 30


# RSI

if rsi > 55:
    buy_score += 25

elif rsi < 45:
    sell_score += 25


# Recent momentum

if momentum > 0:
    buy_score += 25

elif momentum < 0:
    sell_score += 25


# Price relative to EMA20

if price > ema20:
    buy_score += 20

elif price < ema20:
    sell_score += 20


# ==============================
# FINAL SIGNAL
# ==============================

if buy_score >= 70 and buy_score > sell_score:
    signal_type = "BUY"
    signal = "BUY 🟢"
    strength = buy_score

elif sell_score >= 70 and sell_score > buy_score:
    signal_type = "SELL"
    signal = "SELL 🔴"
    strength = sell_score

else:
    signal_type = "NO TRADE"
    signal = "NO TRADE ⚪"
    strength = max(
        buy_score,
        sell_score
    )


# ==============================
# ENTRY / SL / TP
# ==============================

entry = price

if signal_type == "BUY":

    stop_loss = entry - STOP_DISTANCE
    take_profit = entry + TAKE_DISTANCE

elif signal_type == "SELL":

    stop_loss = entry + STOP_DISTANCE
    take_profit = entry - TAKE_DISTANCE

else:

    stop_loss = None
    take_profit = None


# ==============================
# PRICE
# ==============================

st.subheader("💱 EUR/USD")

st.metric(
    "Current Price",
    f"{price:.5f}"
)


# ==============================
# SIGNAL
# ==============================

st.subheader("🤖 Robot Signal")

if signal_type == "BUY":
    st.success(signal)

elif signal_type == "SELL":
    st.error(signal)

else:
    st.warning(signal)


st.metric(
    "Signal Strength",
    f"{strength}%"
)


# ==============================
# MARKET ANALYSIS
# ==============================

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


st.metric(
    "Recent Momentum",
    f"{momentum:.2f}%"
)


# ==============================
# TRADE LEVELS
# ==============================

st.subheader("🎯 Trade Levels")

if signal_type != "NO TRADE":

    st.write(
        f"**Entry:** {entry:.5f}"
    )

    st.write(
        f"**Stop-Loss:** {stop_loss:.5f}"
    )

    st.write(
        f"**Take-Profit:** {take_profit:.5f}"
    )

else:

    st.info(
        "No trade levels because the robot says NO TRADE."
    )


# ==============================
# SIGNAL REASONS
# ==============================

st.subheader("🧠 Signal Reasons")

if signal_type == "BUY":

    if ema20 > ema50:
        st.write("✅ EMA 20 is above EMA 50")

    if rsi > 55:
        st.write("✅ RSI shows bullish momentum")

    if momentum > 0:
        st.write("✅ Recent price momentum is upward")

    if price > ema20:
        st.write("✅ Price is above EMA 20")


elif signal_type == "SELL":

    if ema20 < ema50:
        st.write("🔴 EMA 20 is below EMA 50")

    if rsi < 45:
        st.write("🔴 RSI shows bearish momentum")

    if momentum < 0:
        st.write("🔴 Recent price momentum is downward")

    if price < ema20:
        st.write("🔴 Price is below EMA 20")


else:

    st.write(
        "⚪ The indicators do not provide enough agreement."
    )

    st.write(
        "⚪ Robot is waiting for stronger confirmation."
    )


# ==============================
# ECONOMIC EVENT ANALYSIS
# ==============================

st.subheader("📰 Economic Event Analysis")

st.info(
    "This section provides an event-risk framework. "
    "Check a live economic calendar before trading because "
    "event dates and times can change."
)

events = [
    ("🇺🇸 NFP", "US employment data", "HIGH"),
    ("🇺🇸 CPI", "US inflation data", "HIGH"),
    ("🇺🇸 Federal Reserve", "US interest-rate decision", "HIGH"),
    ("🇪🇺 ECB", "Eurozone interest-rate decision", "HIGH"),
    ("🇪🇺 Eurozone CPI", "Eurozone inflation data", "HIGH"),
    ("🇺🇸 GDP", "US economic growth", "MEDIUM"),
    ("🇪🇺 Eurozone GDP", "Eurozone economic growth", "MEDIUM")
]

for name, description, impact in events:

    st.write(
        f"**{name}** — {description} — "
        f"Impact: **{impact}**"
    )


st.warning(
    "⚠️ High-impact economic releases can cause "
    "large and rapid EUR/USD price movements."
)


# ==============================
# CHART
# ==============================

st.subheader("📈 EUR/USD Chart")

chart_data = data[
    ["Close", "EMA_20", "EMA_50"]
].tail(200)

st.line_chart(chart_data)


# ==============================
# REFRESH
# ==============================

if st.button("🔄 Refresh Analysis"):

    st.cache_data.clear()
    st.rerun()


# ==============================
# FOOTER
# ==============================

st.divider()

st.caption(
    "⚠️ Analysis only. "
    "This robot does not place trades. "
    "Signals and levels are not guaranteed."
)