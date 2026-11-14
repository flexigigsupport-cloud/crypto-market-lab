import numpy as np
import pandas as pd
import pytest
from backtest import run_backtest, run_walk_forward

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
