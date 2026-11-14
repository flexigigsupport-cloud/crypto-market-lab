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
    test_fraction: float = 0.30,
) -> dict:
    """Evaluate a fixed rule on the final chronological holdout segment.

    Indicators are computed causally over the full timeline. The earlier segment
    supplies indicator warm-up/training history only; reported metrics use only
    the final test_fraction of valid return periods. Signals apply one candle later.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Fee and slippage assumptions cannot be negative.")
    if not 0.1 <= test_fraction <= 0.5:
        raise ValueError("test_fraction must be between 0.10 and 0.50.")
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Input data must contain: {', '.join(sorted(required))}")
    if len(frame) < 100:
        raise ValueError("At least 100 candles are required for a chronological holdout test.")
    if (frame["close"] <= 0).any() or not np.isfinite(frame["close"]).all():
        raise ValueError("Closing prices must be finite and greater than zero.")
    if not frame.index.is_monotonic_increasing:
        raise ValueError("Candles must be sorted from oldest to newest.")
    if frame.index.has_duplicates:
        raise ValueError("Candle timestamps must be unique.")

    data = add_indicators(frame).copy()
    if STRATEGIES[strategy] == "sma":
        raw_signal = (data["sma_20"] > data["sma_50"]).astype(float)
        raw_signal[data["sma_20"].isna() | data["sma_50"].isna()] = np.nan
    else:
        raw_signal = (data["rsi_14"] > 50).astype(float)
        raw_signal[data["rsi_14"].isna()] = np.nan

    data["position"] = raw_signal.shift(1)
    data["market_return"] = data["close"].pct_change()
    data = data.dropna(subset=["position", "market_return"]).copy()
    if len(data) < 30:
        raise ValueError("Not enough valid return periods after indicator warm-up.")

    split_at = int(len(data) * (1 - test_fraction))
    training_count = split_at
    test = data.iloc[split_at:].copy()
    if len(test) < 10:
        raise ValueError("Holdout segment is too small; load more historical candles.")

    # Treat the holdout boundary as a fresh paper portfolio, charging entry cost
    # if the first test-period position is exposed.
    turnover = test["position"].diff().abs()
    turnover.iloc[0] = abs(test["position"].iloc[0])
    cost_rate = (fee_bps + slippage_bps) / 10_000
    test["estimated_cost"] = turnover * cost_rate
    test["strategy_return"] = (
        test["position"] * test["market_return"] - test["estimated_cost"]
    )
    test["strategy_equity"] = (1 + test["strategy_return"]).cumprod()
    test["buy_hold_equity"] = (1 + test["market_return"]).cumprod()
    test["drawdown"] = test["strategy_equity"] / test["strategy_equity"].cummax() - 1

    return {
        "strategy": strategy,
        "training_periods": int(training_count),
        "candles_tested": int(len(test)),
        "test_start": str(test.index[0]),
        "test_end": str(test.index[-1]),
        "total_return_pct": float((test["strategy_equity"].iloc[-1] - 1) * 100),
        "buy_hold_return_pct": float((test["buy_hold_equity"].iloc[-1] - 1) * 100),
        "max_drawdown_pct": float(test["drawdown"].min() * 100),
        "positive_periods_pct": float((test["strategy_return"] > 0).mean() * 100),
        "time_in_market_pct": float(test["position"].mean() * 100),
        "position_changes": int((turnover > 0).sum()),
        "assumed_fee_bps": float(fee_bps),
        "assumed_slippage_bps": float(slippage_bps),
        "test_fraction": float(test_fraction),
        "equity_curve": test[["strategy_equity", "buy_hold_equity"]],
        "periods": test[["position", "market_return", "strategy_return", "estimated_cost"]],
        "note": (
            "Metrics use only the final chronological holdout segment. Earlier candles "
            "are used for indicator warm-up and are excluded from reported performance. "
            "This is one holdout, not repeated walk-forward validation or proof of future performance."
        ),
    }
