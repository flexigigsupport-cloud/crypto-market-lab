"""Streamlit UI for Crypto Market Lab. Educational research only."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from analysis import compare_timeframes, educational_assessment, strategy_consensus_research
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
    candle_count = st.slider("Historical candles", 100, 5000, 1200, 100)
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

st.divider()
st.subheader("One-click market research")
st.caption("Creates an educational snapshot from the five available timeframes. It ranks the direction of the evidence; it does not issue a buy/sell instruction or calculate a validated probability.")
if st.button("Analyse market now", type="primary", use_container_width=True):
    try:
        with st.spinner("Comparing completed candles across all five timeframes..."):
            snapshot_frames = {name: fetch_candles(product, name, 120) for name in TIMEFRAMES}
            snapshot = compare_timeframes(snapshot_frames)
            reports = snapshot["reports"]
            total_score = sum(item["score"] for item in reports.values())
            bullish_count = snapshot["bullish_count"]
            bearish_count = snapshot["bearish_count"]
            if total_score >= 3 and bullish_count > bearish_count:
                direction = "Bullish evidence leads"
            elif total_score <= -3 and bearish_count > bullish_count:
                direction = "Bearish evidence leads"
            else:
                direction = "No clear directional agreement"
            strongest = max(reports.items(), key=lambda pair: abs(pair[1]["score"]))
            record = {
                "checked_at": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC"),
                "asset": product,
                "direction": direction,
                "evidence_total": total_score,
                "bullish_timeframes": bullish_count,
                "bearish_timeframes": bearish_count,
                "mixed_timeframes": snapshot["mixed_count"],
                "strongest_timeframe": strongest[0],
                "timeframe_results": ", ".join(f"{name}: {item['label']} ({item['score']:+d})" for name, item in reports.items()),
            }
            history = st.session_state.get("assessment_history", [])
            history.insert(0, record)
            st.session_state.assessment_history = history[:20]
            st.session_state.latest_snapshot = snapshot
    except (MarketDataError, ValueError) as exc:
        st.error(f"Could not complete the assessment: {exc}")

if st.session_state.get("latest_snapshot"):
    snapshot = st.session_state.latest_snapshot
    reports = snapshot["reports"]
    record = st.session_state.assessment_history[0]
    st.markdown(f"### {record['direction']}")
    a, b, c, d = st.columns(4)
    a.metric("Combined evidence", f"{record['evidence_total']:+d} / 15")
    b.metric("Bullish timeframes", str(record["bullish_timeframes"]))
    c.metric("Bearish timeframes", str(record["bearish_timeframes"]))
    d.metric("Mixed timeframes", str(record["mixed_timeframes"]))
    st.caption(f"Strongest single-timeframe evidence: {record['strongest_timeframe']} · Checked {record['checked_at']}")
    st.dataframe([{"Timeframe": name, "Assessment": item["label"], "Evidence score": item["score"], "Patterns": ", ".join(item["patterns"])} for name, item in reports.items()], use_container_width=True, hide_index=True)
    st.info(snapshot["note"])
    st.warning("The combined score is a simple count of indicator agreement, not a probability of a profitable outcome. Do not use it as an instruction to buy, sell or use leverage.")

if st.session_state.get("assessment_history"):
    st.subheader("Last 20 assessment records")
    st.dataframe(st.session_state.assessment_history, use_container_width=True, hide_index=True)
    st.caption("These records are kept in this app session. They are not permanently stored and may reset when the app restarts.")

st.divider()
st.subheader("Final research conclusion")
st.caption("A consolidated interpretation of the selected asset's latest real Coinbase candles. This is descriptive research, not a forecast or trading instruction.")
final_reports = st.session_state.get("latest_snapshot", {}).get("reports")
if final_reports and st.session_state.get("assessment_history") and st.session_state.assessment_history[0].get("asset") == product:
    conclusion_reports = final_reports
    conclusion_label = st.session_state.latest_snapshot["overall"]
    conclusion_source = "Five-timeframe snapshot"
else:
    conclusion_reports = {timeframe: report}
    conclusion_label = report["label"]
    conclusion_source = f"Selected chart timeframe ({timeframe}) only"

bullish_total = sum(item["label"] == "Bullish evidence" for item in conclusion_reports.values())
bearish_total = sum(item["label"] == "Bearish evidence" for item in conclusion_reports.values())
mixed_total = len(conclusion_reports) - bullish_total - bearish_total
if bullish_total > bearish_total and mixed_total == 0:
    final_wording = "Bullish indicator evidence is aligned across the reports available. This describes the observed candles; it does not establish that prices will rise."
elif bearish_total > bullish_total and mixed_total == 0:
    final_wording = "Bearish indicator evidence is aligned across the reports available. This describes the observed candles; it does not establish that prices will fall."
elif bullish_total > bearish_total:
    final_wording = "Bullish evidence is more common, but at least one timeframe is mixed or disagrees. The overall picture is not fully aligned."
elif bearish_total > bullish_total:
    final_wording = "Bearish evidence is more common, but at least one timeframe is mixed or disagrees. The overall picture is not fully aligned."
else:
    final_wording = "The available indicators do not establish a clear directional consensus. Treat the current picture as mixed or inconclusive."

st.markdown(f"**Asset:** {product}  \n**Data source:** Coinbase Exchange public candles  \n**Conclusion basis:** {conclusion_source}  \n**Latest completed candle:** {frame.index[-1].strftime('%Y-%m-%d %H:%M UTC')}")
st.markdown(f"**Final conclusion:** {final_wording}")
st.write(f"**Timeframe count:** {bullish_total} bullish · {bearish_total} bearish · {mixed_total} mixed")
st.write("**Current-chart evidence:** " + ("; ".join(report["evidence"]) if report["evidence"] else "No decisive indicator evidence on the selected timeframe."))
st.write("**Latest candle observations:** " + "; ".join(report["patterns"]))
if pd.notna(latest["atr_14"]) and latest["close"]:
    st.write(f"**Recent volatility context:** ATR(14) is {latest['atr_14']:.6g} price units, approximately {latest['atr_14'] / latest['close'] * 100:.2f}% of the latest close. ATR measures recent movement; it does not set a safe target or predict direction.")
st.write("**Take-profit (TP):** Not generated. A target intended to guide a real trade would be an actionable trading instruction, and these uncalibrated indicators cannot justify one. For research, use the historical simulation results below to study how past price paths behaved under explicit, retrospective assumptions.")
st.caption("Limitations: indicator thresholds are simple and uncalibrated; candle patterns are context-dependent; timeframes are not independent evidence; fees, slippage, liquidity and exchange differences can change historical results. No probability of success is implied.")


st.divider()
st.subheader("Multi-strategy research engine")
st.caption("Runs several descriptive research lenses on fresh, completed Coinbase candles across all five timeframes. It does not generate orders, entry instructions, take-profit targets or execution signals.")
if st.button("Run multi-strategy research", type="primary", use_container_width=True):
    try:
        with st.spinner("Running trend, momentum, candle, volume and volatility research across five timeframes..."):
            strategy_results = {}
            for name in TIMEFRAMES:
                research_frame = fetch_candles(product, name, 180)
                strategy_results[name] = strategy_consensus_research(research_frame)
            st.session_state.strategy_research = {
                "asset": product,
                "checked_at": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC"),
                "results": strategy_results,
            }
    except (MarketDataError, ValueError) as exc:
        st.error(f"Multi-strategy analysis could not be completed: {exc}")

strategy_snapshot = st.session_state.get("strategy_research")
if strategy_snapshot and strategy_snapshot.get("asset") == product:
    strategy_results = strategy_snapshot["results"]
    bullish_tf = sum(item["overall"] == "Bullish evidence leads" for item in strategy_results.values())
    bearish_tf = sum(item["overall"] == "Bearish evidence leads" for item in strategy_results.values())
    if bullish_tf > bearish_tf and bullish_tf >= 2:
        st.markdown("### Bullish evidence leads across the timeframe research")
    elif bearish_tf > bullish_tf and bearish_tf >= 2:
        st.markdown("### Bearish evidence leads across the timeframe research")
    else:
        st.markdown("### Mixed evidence — no clear multi-timeframe consensus")
    st.caption(f"Asset: {product} · Completed: {strategy_snapshot['checked_at']} · {bullish_tf} bullish timeframe assessments · {bearish_tf} bearish · {5 - bullish_tf - bearish_tf} mixed")
    summary_rows = []
    detail_rows = []
    range_rows = []
    for name, result in strategy_results.items():
        summary_rows.append({
            "Timeframe": name,
            "Overall research": result["overall"],
            "Bullish lenses": result["bullish_lenses"],
            "Bearish lenses": result["bearish_lenses"],
            "Neutral lenses": result["neutral_lenses"],
        })
        for lens in result["lenses"]:
            detail_rows.append({
                "Timeframe": name,
                "Research lens": lens["strategy"],
                "Evidence classification": lens["bias"],
                "Explanation": lens["reason"],
            })
        observed = result["historical_range_context"]
        range_rows.append({
            "Timeframe": name,
            "50-candle observed low": observed["observed_low"],
            "50-candle observed high": observed["observed_high"],
            "Latest close": observed["latest_close"],
        })
    st.dataframe(summary_rows, use_container_width=True, hide_index=True)
    st.markdown("**Strategy-by-strategy reasoning**")
    st.dataframe(detail_rows, use_container_width=True, hide_index=True)
    st.markdown("**Recent historical range context (not price targets)**")
    st.dataframe(range_rows, use_container_width=True, hide_index=True)
    st.info(strategy_results["1h"]["note"])
    st.warning("This is a research classification, not a buy/sell command or TP recommendation. Historical highs/lows are descriptive only. Counts are not calibrated probabilities, and multiple lenses can agree because they use overlapping market information.")

st.divider()
st.subheader("Long-range historical market context")
st.write("Load up to 5,000 completed daily candles for the selected asset. This gives a long-range view where the exchange has data; it does not guarantee 10–20 years of coverage.")
if st.button("Load maximum available daily history"):
    try:
        with st.spinner("Retrieving up to 5,000 daily candles..."):
            long_history = fetch_candles_history(product, "1d", 5000)
            st.session_state.long_history = long_history
    except (MarketDataError, ValueError) as exc:
        st.error(str(exc))
if st.session_state.get("long_history") is not None:
    long_history = st.session_state.long_history
    first_date = long_history.index.min()
    last_date = long_history.index.max()
    years = (last_date - first_date).days / 365.25
    st.metric("Actual daily-history coverage", f"{years:.1f} years")
    st.caption(f"{len(long_history):,} completed daily candles · {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')} UTC. Coverage depends on the asset's listing date and Coinbase data availability.")
    history_fig = go.Figure()
    history_fig.add_trace(go.Scatter(x=long_history.index, y=long_history["close"], name="Daily close"))
    history_fig.update_layout(height=360, xaxis_title="Date", yaxis_title="Price (USD)")
    st.plotly_chart(history_fig, use_container_width=True)

st.caption(f"Last completed candle: {frame.index[-1].strftime('%Y-%m-%d %H:%M UTC')} · Coinbase public market data.")
