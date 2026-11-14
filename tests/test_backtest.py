import numpy as np
import pandas as pd
import pytest

from backtest import run_backtest


def sample_frame(length=240):
    close = 100 + np.cumsum(np.sin(np.arange(length) / 5) * 0.4 + 0.12)
    return pd.DataFrame({
        "open": close - 0.2,
        "high": close + 1,
        "low": close - 1,
        "close": close,
        "volume": 1000,
    }, index=pd.date_range("2025-01-01", periods=length, freq="h", tz="UTC"))


def test_backtest_reports_chronological_holdout_metrics():
    result = run_backtest(sample_frame())
    assert result["candles_tested"] > 0
    assert result["training_periods"] > result["candles_tested"]
    assert result["test_start"] < result["test_end"]
    assert "max_drawdown_pct" in result
    assert "strategy_equity" in result["equity_curve"]
    assert result["assumed_fee_bps"] == 10
    assert result["assumed_slippage_bps"] == 5


def test_holdout_fraction_changes_test_size():
    frame = sample_frame()
    small = run_backtest(frame, test_fraction=0.2)
    large = run_backtest(frame, test_fraction=0.4)
    assert large["candles_tested"] > small["candles_tested"]


def test_backtest_applies_signal_on_following_candle():
    result = run_backtest(sample_frame(), fee_bps=0, slippage_bps=0)
    assert result["periods"]["position"].isin([0.0, 1.0]).all()
    assert result["periods"]["market_return"].notna().all()


def test_backtest_rejects_invalid_parameters_and_data():
    frame = sample_frame()
    with pytest.raises(ValueError):
        run_backtest(frame, strategy="Mystery")
    with pytest.raises(ValueError):
        run_backtest(frame, fee_bps=-1)
    with pytest.raises(ValueError):
        run_backtest(frame, test_fraction=0.8)
    with pytest.raises(ValueError):
        run_backtest(frame.iloc[::-1])


def test_backtest_rejects_short_history():
    with pytest.raises(ValueError):
        run_backtest(sample_frame(80))
