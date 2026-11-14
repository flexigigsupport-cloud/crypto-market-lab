"""Historical paper-only simulations. No live trading functionality."""
from __future__ import annotations
import numpy as np
import pandas as pd
from analysis import add_indicators

STRATEGIES = {"SMA trend filter": "sma", "RSI momentum filter": "rsi"}


def _prepare(frame, strategy):
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}")
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Input data must contain: {', '.join(sorted(required))}")
    if len(frame) < 100:
        raise ValueError("At least 100 candles are required.")
    if (frame["close"] <= 0).any() or not np.isfinite(frame["close"]).all():
        raise ValueError("Closing prices must be finite and positive.")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Candles must be oldest-to-newest with unique timestamps.")
    data = add_indicators(frame).copy()
    if STRATEGIES[strategy] == "sma":
        signal = (data["sma_20"] > data["sma_50"]).astype(float)
        signal[data["sma_20"].isna() | data["sma_50"].isna()] = np.nan
    else:
        signal = (data["rsi_14"] > 50).astype(float)
        signal[data["rsi_14"].isna()] = np.nan
    data["position"] = signal.shift(1)
    data["market_return"] = data["close"].pct_change()
    data = data.dropna(subset=["position", "market_return"]).copy()
    if len(data) < 60:
        raise ValueError("Not enough valid return periods after indicator warm-up.")
    return data


def _metrics(test, fee_bps, slippage_bps):
    turnover = test["position"].diff().abs()
    if len(turnover):
        turnover.iloc[0] = abs(test["position"].iloc[0])
    test = test.copy()
    test["estimated_cost"] = turnover * ((fee_bps + slippage_bps) / 10000)
    test["strategy_return"] = test["position"] * test["market_return"] - test["estimated_cost"]
    test["strategy_equity"] = (1 + test["strategy_return"]).cumprod()
    test["buy_hold_equity"] = (1 + test["market_return"]).cumprod()
    test["drawdown"] = test["strategy_equity"] / test["strategy_equity"].cummax() - 1
    return {
        "candles_tested": int(len(test)),
        "total_return_pct": float((test["strategy_equity"].iloc[-1] - 1) * 100),
        "buy_hold_return_pct": float((test["buy_hold_equity"].iloc[-1] - 1) * 100),
        "max_drawdown_pct": float(test["drawdown"].min() * 100),
        "positive_periods_pct": float((test["strategy_return"] > 0).mean() * 100),
        "time_in_market_pct": float(test["position"].mean() * 100),
        "position_changes": int((turnover > 0).sum()),
        "equity_curve": test[["strategy_equity", "buy_hold_equity"]],
        "periods": test[["position", "market_return", "strategy_return", "estimated_cost"]],
    }


def run_backtest(frame, strategy="SMA trend filter", fee_bps=10.0,
                 slippage_bps=5.0, test_fraction=0.30):
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Costs cannot be negative.")
    if not 0.1 <= test_fraction <= 0.5:
        raise ValueError("test_fraction must be between 0.10 and 0.50.")
    data = _prepare(frame, strategy)
    split = int(len(data) * (1 - test_fraction))
    test = data.iloc[split:].copy()
    if len(test) < 10:
        raise ValueError("Holdout too small; load more history.")
    result = _metrics(test, fee_bps, slippage_bps)
    result.update({
        "strategy": strategy, "training_periods": int(split),
        "test_start": str(test.index[0]), "test_end": str(test.index[-1]),
        "assumed_fee_bps": float(fee_bps), "assumed_slippage_bps": float(slippage_bps),
        "note": "One chronological holdout only; not proof of future performance.",
    })
    return result


def run_walk_forward(frame, strategy="SMA trend filter", fee_bps=10.0,
                     slippage_bps=5.0, folds=4, initial_train_fraction=0.5):
    """Evaluate a fixed rule on sequential later folds; no tuning on test folds."""
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Costs cannot be negative.")
    if not 2 <= folds <= 8:
        raise ValueError("folds must be between 2 and 8.")
    if not 0.3 <= initial_train_fraction <= 0.8:
        raise ValueError("initial_train_fraction must be between 0.30 and 0.80.")
    data = _prepare(frame, strategy)
    first = int(len(data) * initial_train_fraction)
    if len(data) - first < folds * 10:
        raise ValueError("Load more history or reduce folds; each fold needs 10+ periods.")
    chunks = [x for x in np.array_split(np.arange(first, len(data)), folds)]
    if any(len(x) < 10 for x in chunks):
        raise ValueError("Each test fold needs at least 10 periods.")
    test = data.iloc[first:].copy()
    result = _metrics(test, fee_bps, slippage_bps)
    fold_rows = []
    for i, indexes in enumerate(chunks, 1):
        part = data.iloc[indexes].copy()
        m = _metrics(part, fee_bps, slippage_bps)
        fold_rows.append({
            "fold": i, "history_periods_before_fold": int(indexes[0]),
            "test_periods": m["candles_tested"], "return_pct": m["total_return_pct"],
            "buy_hold_pct": m["buy_hold_return_pct"], "max_drawdown_pct": m["max_drawdown_pct"],
            "position_changes": m["position_changes"], "start": str(part.index[0]),
            "end": str(part.index[-1]),
        })
    result.update({
        "strategy": strategy, "initial_history_periods": int(first),
        "folds": fold_rows, "test_start": str(test.index[0]), "test_end": str(test.index[-1]),
        "assumed_fee_bps": float(fee_bps), "assumed_slippage_bps": float(slippage_bps),
        "note": "Sequential walk-forward evaluation of a fixed rule; not a forecast or guarantee.",
    })
    return result
