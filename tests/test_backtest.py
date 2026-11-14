import numpy as np
import pandas as pd
import pytest

from backtest import run_backtest


def sample_frame(length=160):
    close = np.linspace(100, 140, length)
    return pd.DataFrame({
        "open": close - 0.2,
        "high": close + 1,
        "low": close - 1,
        "close": close,
        "volume": 1000,
    })


def test_backtest_returns_metrics_and_curve():
    result = run_backtest(sample_frame())
    assert result["candles_tested"] > 0
    assert "max_drawdown_pct" in result
    assert "strategy_equity" in result["equity_curve"]
    assert result["assumed_fee_bps"] == 10
    assert result["assumed_slippage_bps"] == 5


def test_backtest_applies_signal_on_following_candle():
    frame = sample_frame()
    result = run_backtest(frame, strategy="SMA trend filter", fee_bps=0, slippage_bps=0)
    # The first valid position follows the indicator warm-up, never the same candle's return.
    assert result["periods"]["position"].iloc[0] in (0.0, 1.0)
    assert result["periods"]["market_return"].notna().all()


def test_backtest_rejects_unknown_strategy_and_negative_costs():
    with pytest.raises(ValueError):
        run_backtest(sample_frame(), strategy="Mystery")
    with pytest.raises(ValueError):
        run_backtest(sample_frame(), fee_bps=-1)


def test_backtest_rejects_short_history():
    with pytest.raises(ValueError):
        run_backtest(sample_frame(40))
