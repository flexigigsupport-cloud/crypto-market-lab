import numpy as np
import pandas as pd
import pytest
from backtest import compare_strategy_history, run_backtest, run_walk_forward

def sample_frame(length=1200):
    close = 100 + np.cumsum(np.sin(np.arange(length) / 5) * 0.4 + 0.12)
    return pd.DataFrame({"open": close - 0.2, "high": close + 1, "low": close - 1, "close": close, "volume": 1000},
                        index=pd.date_range("2025-01-01", periods=length, freq="h", tz="UTC"))

def test_holdout_metrics():
    result = run_backtest(sample_frame())
    assert result["candles_tested"] > 0
    assert result["training_periods"] > result["candles_tested"]
    assert result["test_start"] < result["test_end"]

def test_walk_forward_sequential_folds():
    result = run_walk_forward(sample_frame(), folds=4)
    assert len(result["folds"]) == 4
    assert result["candles_tested"] == sum(row["test_periods"] for row in result["folds"])
    assert result["folds"][0]["end"] < result["folds"][1]["start"]

def test_walk_forward_validation_errors():
    with pytest.raises(ValueError):
        run_walk_forward(sample_frame(), folds=1)
    with pytest.raises(ValueError):
        run_walk_forward(sample_frame(200), folds=8)

def test_invalid_backtest_inputs():
    frame = sample_frame()
    with pytest.raises(ValueError):
        run_backtest(frame, strategy="unknown")
    with pytest.raises(ValueError):
        run_backtest(frame, fee_bps=-1)
    with pytest.raises(ValueError):
        run_backtest(frame.iloc[::-1])



def test_automatic_strategy_comparison_keeps_holdout_separate():
    result = compare_strategy_history(sample_frame(1600))
    assert result["selected_historical_candidate"] in {
        "SMA trend filter",
        "RSI momentum filter",
        "MACD momentum filter",
        "20-candle breakout filter",
        "RSI mean-reversion filter",
    }
    assert len(result["rankings"]) == 5
    assert result["holdout_periods"] > 0
    assert set(result["holdout_results"]) == {row["strategy"] for row in result["rankings"]}
    assert "not a current buy/sell recommendation" in result["note"]


def test_strategy_comparison_rejects_invalid_training_share():
    with pytest.raises(ValueError):
        compare_strategy_history(sample_frame(), training_fraction=0.5)
