"""Streamlit UI for Crypto Market Lab. Educational research only."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from analysis import compare_timeframes, educational_assessment
from backtest import STRATEGIES, run_backtest, run_walk_forward
from market_data import MarketDataError, PRODUCTS, TIMEFRAMES, fetch_candles, fetch_candles_history

st.set_page_config(page_title="Crypto Market Lab", page_icon="📊", layout="wide")
st.title("Crypto Market Lab")
st.caption("Read-only public market data · Candlestick research · Historical paper simulations")
st.warning("Educational research only. No exchange accounts, deposits, live orders or execution are connected. Outputs are uncertain and are not trading instructions.")

with st.sidebar:
    st.header("Market")
    product = st.selectbox("Asset", PRODUCTS)
    timeframe = st.selectbox("Chart timeframe", list(TIMEFRAMES.keys()), index=1)
    candle_count = st.slider("Historical candles", 100, 3000, 1200, 100)
    refresh = st.button("Refresh market data", type="primary")

if "market_frame" not in st.session_state:
    st.session_state.market_frame = None
    st.session_state.market_key = None
key = (product, timeframe, candle_count)
if refresh or st.session_state.market_frame is None or st.session_state.market_key != key:
    with st.spinner(f"Loading up to {candle_count:,} completed candles..."):
        try:
            frame = fetch_candles(product, timeframe, candle_count) if candle_count <= 300 else fetch_candles_history(product, timeframe, candle_count)
            st.session_state.market_frame = frame
            st.session_state.market_key = key
            st.session_state.backtest_result = None
            st.session_state.walk_forward_result = None
        except (MarketDataError, ValueError) as exc:
            st.error(str(exc))
            st.stop()

frame = st.session_state.market_frame
report = educational_assessment(frame)
indicators = report["indicators"]
latest = indicators.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest close", f"${latest['close']:,.4f}")
c2.metric("RSI (14)", "—" if pd.isna(latest["rsi_14"]) else f"{latest['rsi_14']:.1f}")
c3.metric("Research assessment", report["label"])
c4.metric("Evidence score", f"{report['score']:+d} / 3")

st.subheader(f"{product} · {timeframe}")
fig = go.Figure()
fig.add_trace(go.Candlestick(x=frame.index, open=frame.open, high=frame.high, low=frame.low, close=frame.close, name="OHLC"))
fig.add_trace(go.Scatter(x=indicators.index, y=indicators.sma_20, name="SMA 20"))
fig.add_trace(go.Scatter(x=indicators.index, y=indicators.sma_50, name="SMA 50"))
fig.update_layout(height=520, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Candlestick observations")
    for pattern in report["patterns"]:
        st.write(f"- {pattern}")
with right:
    st.subheader("Indicator evidence")
    for evidence in report["evidence"] or ["No clear indicator evidence yet."]:
        st.write(f"- {evidence}")
    for caution in report["cautions"]:
        st.caption(caution)
st.subheader("RSI, MACD and ATR")
st.line_chart(indicators[["rsi_14"]].dropna(), height=160)
st.line_chart(indicators[["macd", "macd_signal"]].dropna(), height=160)
st.line_chart(indicators[["atr_14"]].dropna(), height=140)

st.divider()
st.subheader("Historical paper simulations")
with st.expander("Simulation settings", expanded=True):
    strategy = st.selectbox("Research rule", list(STRATEGIES.keys()))
    fee = st.number_input("Assumed fee per position change (bps)", 0.0, 500.0, 10.0, 1.0)
    slip = st.number_input("Assumed slippage per position change (bps)", 0.0, 500.0, 5.0, 1.0)
    holdout = st.slider("Single holdout share", 0.1, 0.5, 0.3, 0.05)
    folds = st.select_slider("Walk-forward folds", [2, 3, 4, 5, 6, 7, 8], value=4)
    train_share = st.slider("Initial history share", 0.3, 0.8, 0.5, 0.05)
    do_holdout = st.button("Run single holdout")
    do_walk = st.button("Run walk-forward validation")
if do_holdout:
    try:
        st.session_state.backtest_result = run_backtest(frame, strategy, fee, slip, holdout)
    except ValueError as exc:
        st.error(str(exc))
if do_walk:
    try:
        st.session_state.walk_forward_result = run_walk_forward(frame, strategy, fee, slip, folds, train_share)
    except ValueError as exc:
        st.error(str(exc))

def show_result(result, heading):
    st.subheader(heading)
    a, b, c, d = st.columns(4)
    a.metric("Simulated return", f"{result['total_return_pct']:.2f}%")
    b.metric("Buy-and-hold", f"{result['buy_hold_return_pct']:.2f}%")
    c.metric("Maximum drawdown", f"{result['max_drawdown_pct']:.2f}%")
    d.metric("Position changes", str(result["position_changes"]))
    st.line_chart(result["equity_curve"], height=240)
    st.caption(f"{result['candles_tested']} periods · {result['test_start']} to {result['test_end']} · fee {result['assumed_fee_bps']} bps · slippage {result['assumed_slippage_bps']} bps")
    st.info(result["note"])
if st.session_state.get("backtest_result"):
    show_result(st.session_state.backtest_result, "Single chronological holdout")
if st.session_state.get("walk_forward_result"):
    result = st.session_state.walk_forward_result
    show_result(result, "Walk-forward validation")
    st.dataframe(result["folds"], use_container_width=True, hide_index=True)
    st.warning("Walk-forward results still depend on the dataset and simplified assumptions. They do not prove predictive power.")

st.divider()
st.subheader("Multi-timeframe research")
if st.button("Compare 5m, 15m, 1h, 6h and 1d"):
    try:
        st.session_state.timeframe_comparison = { "result": compare_timeframes({name: fetch_candles(product, name, 120) for name in TIMEFRAMES}) }
    except (MarketDataError, ValueError) as exc:
        st.error(str(exc))
comparison = st.session_state.get("timeframe_comparison")
if comparison:
    result = comparison["result"]
    st.metric("Overall timeframe picture", result["overall"])
    st.caption(result["note"])
    st.dataframe([{"Timeframe": name, "Assessment": item["label"], "Score": item["score"], "Patterns": ", ".join(item["patterns"])} for name, item in result["reports"].items()], use_container_width=True, hide_index=True)

st.caption(f"Last completed candle: {frame.index[-1].strftime('%Y-%m-%d %H:%M UTC')} · Coinbase public market data.")
