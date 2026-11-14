"""Historical, paper-only strategy simulations. No live trading functionality."""

from __future__ import annotations

import numpy as np
import pandas as pd

from analysis import add_indicators


STRATEGIES = {
    "SMA trend filter": "sma",
    "RSI momentum filter": "rsi",
}


def run_backtest(
    frame: pd.DataFrame,
    strategy: str = "SMA trend filter",
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict:
    """Simulate long/flat exposure using only information available at each close.

    A signal calculated from candle t is applied to candle t+1's return.
    Costs are charged on each unit of position turnover, including entry/exit.
    This is a simplified educational model, not an execution or forecasting tool.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Fee and slippage assumptions cannot be negative.")
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Input data must contain: {', '.join(sorted(required))}")
    if len(frame) < 55:
        raise ValueError("At least 55 candles are required for this simulation.")
    if (frame["close"] <= 0).any() or not np.isfinite(frame["close"]).all():
        raise ValueError("Closing prices must be finite and greater than zero.")

    data = add_indicators(frame).copy()
    if STRATEGIES[strategy] == "sma":
        raw_signal = (data["sma_20"] > data["sma_50"]).astype(float)
        raw_signal[data["sma_20"].isna() | data["sma_50"].isna()] = np.nan
    else:
        raw_signal = (data["rsi_14"] > 50).astype(float)
        raw_signal[data["rsi_14"].isna()] = np.nan

    # Shift one full candle: today's close-derived signal cannot earn today's return.
    data["position"] = raw_signal.shift(1)
    data["market_return"] = data["close"].pct_change()
    data = data.dropna(subset=["position", "market_return"]).copy()
    if data.empty:
        raise ValueError("Not enough valid indicator history for this simulation.")

    turnover = data["position"].diff().abs()
    if len(turnover):
        turnover.iloc[0] = abs(data["position"].iloc[0])
    cost_rate = (fee_bps + slippage_bps) / 10_000
    data["estimated_cost"] = turnover * cost_rate
    data["strategy_return"] = (
        data["position"] * data["market_return"] - data["estimated_cost"]
    )
    data["strategy_equity"] = (1 + data["strategy_return"]).cumprod()
    data["buy_hold_equity"] = (1 + data["market_return"]).cumprod()
    data["drawdown"] = (
        data["strategy_equity"] / data["strategy_equity"].cummax()
    ) - 1

    total_return = float(data["strategy_equity"].iloc[-1] - 1)
    benchmark_return = float(data["buy_hold_equity"].iloc[-1] - 1)
    max_drawdown = float(data["drawdown"].min())
    position_changes = int((turnover > 0).sum())

    return {
        "strategy": strategy,
        "candles_tested": int(len(data)),
        "total_return_pct": total_return * 100,
        "buy_hold_return_pct": benchmark_return * 100,
        "max_drawdown_pct": max_drawdown * 100,
        "positive_periods_pct": float((data["strategy_return"] > 0).mean() * 100),
        "time_in_market_pct": float(data["position"].mean() * 100),
        "position_changes": position_changes,
        "assumed_fee_bps": float(fee_bps),
        "assumed_slippage_bps": float(slippage_bps),
        "equity_curve": data[["strategy_equity", "buy_hold_equity"]],
        "periods": data[["position", "market_return", "strategy_return", "estimated_cost"]],
        "note": (
            "Historical simulation only. Results depend on the selected dates, "
            "assumed costs, data quality and simplified execution model. "
            "They are not forecasts or recommendations."
        ),
    }
