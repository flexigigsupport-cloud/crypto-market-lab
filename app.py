"""Streamlit UI for Crypto Market Lab. Educational research only."""

import plotly.graph_objects as go
import streamlit as st

from analysis import educational_assessment
from market_data import MarketDataError, PRODUCTS, TIMEFRAMES, fetch_candles

st.set_page_config(page_title="Crypto Market Lab", page_icon="📊", layout="wide")
st.title("Crypto Market Lab")
st.caption("Live public market data • Candlestick research • Multi-timeframe groundwork")

st.warning(
    "Educational research only. Assessments are uncertain summaries, not buy/sell "
    "instructions. No trading accounts or order execution are connected."
)

with st.sidebar:
    st.header("Market")
    product = st.selectbox("Asset", PRODUCTS)
    timeframe = st.selectbox("Timeframe", list(TIMEFRAMES.keys()), index=1)
    candle_count = st.slider("Candles to load", min_value=50, max_value=300, value=200, step=25)
    refresh = st.button("Refresh market data", type="primary")

if "market_frame" not in st.session_state:
    st.session_state.market_frame = None
    st.session_state.market_key = None

key = (product, timeframe, candle_count)
if refresh or st.session_state.market_frame is None or st.session_state.market_key != key:
    with st.spinner("Retrieving public candle data..."):
        try:
            st.session_state.market_frame = fetch_candles(product, timeframe, candle_count)
            st.session_state.market_key = key
        except (MarketDataError, ValueError) as exc:
            st.error(str(exc))
            st.stop()

frame = st.session_state.market_frame
report = educational_assessment(frame)
indicators = report["indicators"]
latest = indicators.iloc[-1]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest close", f"${latest['close']:,.4f}")
col2.metric("RSI (14)", "—" if latest["rsi_14"] != latest["rsi_14"] else f"{latest['rsi_14']:.1f}")
col3.metric("Research assessment", report["label"])
col4.metric("Evidence score", f"{report['score']:+d} / 3")

st.subheader(f"{product} · {timeframe}")
chart = go.Figure()
chart.add_trace(go.Candlestick(
    x=frame.index,
    open=frame["open"],
    high=frame["high"],
    low=frame["low"],
    close=frame["close"],
    name="OHLC",
))
chart.add_trace(go.Scatter(x=indicators.index, y=indicators["sma_20"], name="SMA 20"))
chart.add_trace(go.Scatter(x=indicators.index, y=indicators["sma_50"], name="SMA 50"))
chart.update_layout(height=560, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=25, b=10))
st.plotly_chart(chart, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Candlestick observations")
    for pattern in report["patterns"]:
        st.write(f"- {pattern}")
with right:
    st.subheader("Indicator evidence")
    if report["evidence"]:
        for item in report["evidence"]:
            st.write(f"- {item}")
    else:
        st.write("No clear indicator evidence yet.")
    for item in report["cautions"]:
        st.caption(f"Note: {item}")

st.subheader("RSI and MACD")
st.line_chart(indicators[["rsi_14"]].dropna(), height=180)
st.line_chart(indicators[["macd", "macd_signal"]].dropna(), height=180)

st.caption(
    f"Last candle timestamp: {frame.index[-1].strftime('%Y-%m-%d %H:%M UTC')} · "
    "Data is supplied by Coinbase Exchange public market-data endpoints."
)
