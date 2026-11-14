"""Streamlit UI for Crypto Market Lab. Educational research only."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis import compare_timeframes, educational_assessment
from backtest import STRATEGIES, run_backtest
from market_data import MarketDataError, PRODUCTS, TIMEFRAMES, fetch_candles

st.set_page_config(page_title="Crypto Market Lab", page_icon="📊", layout="wide")
st.title("Crypto Market Lab")
st.caption("Public crypto market data • Candlestick research • Multi-timeframe comparison")
st.warning(
    "Educational research and historical simulation only. Assessments are uncertain "
    "summaries, not buy/sell instructions. No trading accounts or order execution are connected."
)

with st.sidebar:
    st.header("Market")
    product = st.selectbox("Asset", PRODUCTS)
    timeframe = st.selectbox("Main chart timeframe", list(TIMEFRAMES.keys()), index=1)
    candle_count = st.slider("Candles to load", min_value=100, max_value=300, value=250, step=25)
    refresh = st.button("Refresh market data", type="primary")

if "market_frame" not in st.session_state:
    st.session_state.market_frame = None
    st.session_state.market_key = None

key = (product, timeframe, candle_count)
if refresh or st.session_state.market_frame is None or st.session_state.market_key != key:
    with st.spinner("Retrieving completed public candles..."):
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
col2.metric("RSI (14)", "—" if pd.isna(latest["rsi_14"]) else f"{latest['rsi_14']:.1f}")
col3.metric("Research assessment", report["label"])
col4.metric("Evidence score", f"{report['score']:+d} / 3")

st.subheader(f"{product} · {timeframe}")
chart = go.Figure()
chart.add_trace(go.Candlestick(
    x=frame.index, open=frame["open"], high=frame["high"],
    low=frame["low"], close=frame["close"], name="OHLC",
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

st.subheader("RSI, MACD and ATR")
st.line_chart(indicators[["rsi_14"]].dropna(), height=180)
st.line_chart(indicators[["macd", "macd_signal"]].dropna(), height=180)
st.line_chart(indicators[["atr_14"]].dropna(), height=150)

st.divider()
st.subheader("Chronological holdout paper backtest")
st.write(
    "The simulator uses earlier candles to warm up indicators, then reports results only "
    "on the later holdout segment. Signals apply to the following candle. This is a "
    "basic chronological holdout—not repeated walk-forward validation."
)
with st.expander("Simulation assumptions", expanded=True):
    chosen_strategy = st.selectbox("Research rule", list(STRATEGIES.keys()))
    test_fraction = st.slider("Final holdout share", min_value=0.1, max_value=0.5, value=0.3, step=0.05)
    fee_bps = st.number_input("Assumed fee per position change (basis points)", min_value=0.0, max_value=500.0, value=10.0, step=1.0)
    slippage_bps = st.number_input("Assumed slippage per position change (basis points)", min_value=0.0, max_value=500.0, value=5.0, step=1.0)
    run_simulation = st.button("Run holdout simulation")

if run_simulation:
    try:
        st.session_state.backtest_result = run_backtest(
            frame, strategy=chosen_strategy, fee_bps=fee_bps,
            slippage_bps=slippage_bps, test_fraction=test_fraction,
        )
    except ValueError as exc:
        st.error(str(exc))

backtest_result = st.session_state.get("backtest_result")
if backtest_result:
    st.caption(
        f"{backtest_result['strategy']} · {backtest_result['training_periods']} earlier "
        f"periods excluded · {backtest_result['candles_tested']} holdout periods · "
        f"{backtest_result['test_start']} to {backtest_result['test_end']}"
    )
    metrics = st.columns(4)
    metrics[0].metric("Holdout return", f"{backtest_result['total_return_pct']:.2f}%")
    metrics[1].metric("Holdout buy-and-hold", f"{backtest_result['buy_hold_return_pct']:.2f}%")
    metrics[2].metric("Maximum drawdown", f"{backtest_result['max_drawdown_pct']:.2f}%")
    metrics[3].metric("Position changes", str(backtest_result["position_changes"]))
    st.line_chart(backtest_result["equity_curve"], height=280)
    st.write({
        "Positive periods": f"{backtest_result['positive_periods_pct']:.1f}%",
        "Time with simulated exposure": f"{backtest_result['time_in_market_pct']:.1f}%",
        "Assumed fee": f"{backtest_result['assumed_fee_bps']:.1f} bps",
        "Assumed slippage": f"{backtest_result['assumed_slippage_bps']:.1f} bps",
    })
    st.info(backtest_result["note"])
    st.warning(
        "A single holdout can still be misleading, especially with a small dataset. "
        "Do not treat a favourable result as evidence that the rule will work in future markets."
    )

st.divider()
st.subheader("Multi-timeframe research")
st.write("Compare the same asset across 5m, 15m, 1h, 6h and 1d. Agreement is not certainty.")
if st.button("Compare all timeframes"):
    timeframe_frames = {}
    try:
        with st.spinner("Loading each timeframe..."):
            for name in TIMEFRAMES:
                timeframe_frames[name] = fetch_candles(product, name, 120)
        st.session_state.timeframe_comparison = compare_timeframes(timeframe_frames)
    except (MarketDataError, ValueError) as exc:
        st.error(f"Could not complete timeframe comparison: {exc}")

comparison = st.session_state.get("timeframe_comparison")
if comparison:
    st.metric("Overall timeframe picture", comparison["overall"])
    st.caption(comparison["note"])
    rows = [{
        "Timeframe": name, "Assessment": item["label"],
        "Evidence score": item["score"], "Latest patterns": ", ".join(item["patterns"]),
    } for name, item in comparison["reports"].items()]
    st.dataframe(rows, use_container_width=True, hide_index=True)

st.caption(
    f"Last completed candle: {frame.index[-1].strftime('%Y-%m-%d %H:%M UTC')} · "
    "Source: Coinbase Exchange public market-data endpoint."
)
