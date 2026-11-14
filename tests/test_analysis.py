import numpy as np
import pandas as pd

from analysis import (
    add_indicators,
    compare_timeframes,
    detect_latest_patterns,
    educational_assessment,
)


def candles(rows):
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])


def test_indicator_columns_are_added():
    close = np.linspace(100, 130, 80)
    frame = pd.DataFrame({
        "open": close - 0.2,
        "high": close + 1,
        "low": close - 1,
        "close": close,
        "volume": 1000,
    })
    result = add_indicators(frame)
    for name in ["sma_20", "sma_50", "rsi_14", "macd", "macd_signal", "atr_14"]:
        assert name in result.columns
    assert result["atr_14"].dropna().ge(0).all()


def test_bullish_engulfing_is_detected():
    frame = candles([
        [10, 10.5, 8.5, 9, 100],
        [8.8, 11.2, 8.6, 10.8, 120],
    ])
    assert "Bullish engulfing" in detect_latest_patterns(frame)


def test_bearish_engulfing_is_detected():
    frame = candles([
        [9, 10.5, 8.8, 10, 100],
        [10.2, 10.4, 8.4, 8.7, 120],
    ])
    assert "Bearish engulfing" in detect_latest_patterns(frame)


def test_inside_bar_is_detected():
    frame = candles([
        [10, 12, 9, 11, 100],
        [10.8, 11.5, 9.5, 10.7, 110],
    ])
    assert "Inside bar" in detect_latest_patterns(frame)


def test_timeframe_comparison_identifies_conflict():
    rising = np.linspace(100, 130, 80)
    falling = np.linspace(130, 100, 80)

    def make_series(values):
        return pd.DataFrame({
            "open": values - 0.1,
            "high": values + 0.8,
            "low": values - 0.8,
            "close": values,
            "volume": 500,
        })

    result = compare_timeframes({"15m": make_series(rising), "4h": make_series(falling)})
    assert result["overall"] == "Timeframes disagree"
    assert result["bullish_count"] == 1
    assert result["bearish_count"] == 1


def test_assessment_is_not_a_probability():
    values = np.linspace(100, 120, 80)
    frame = pd.DataFrame({
        "open": values - 0.1,
        "high": values + 1,
        "low": values - 1,
        "close": values,
        "volume": 1000,
    })
    report = educational_assessment(frame)
    assert "score" in report
    assert "patterns" in report
    assert any("not statistically calibrated" in note for note in report["cautions"])


def test_strategy_consensus_research_returns_transparent_lenses():
    from analysis import strategy_consensus_research

    values = np.linspace(100, 145, 100)
    frame = pd.DataFrame({
        "open": values - 0.15,
        "high": values + 1,
        "low": values - 1,
        "close": values,
        "volume": np.full(100, 1000.0),
    })
    result = strategy_consensus_research(frame)
    assert result["overall"] in {
        "Bullish evidence leads",
        "Bearish evidence leads",
        "Mixed / no clear consensus",
    }
    assert {"Trend structure", "RSI momentum", "MACD momentum", "Candlestick structure"} <= {
        item["strategy"] for item in result["lenses"]
    }
    assert result["historical_range_context"]["lookback_candles"] == 50
    assert "not probabilities" in result["note"]
