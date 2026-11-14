"""Transparent technical-analysis helpers for educational research."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """Return OHLCV data with common, transparent indicators."""
    result = frame.copy()
    close = result["close"]

    result["sma_20"] = close.rolling(20).mean()
    result["sma_50"] = close.rolling(50).mean()

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    relative_strength = avg_gain / avg_loss.replace(0, np.nan)
    result["rsi_14"] = 100 - (100 / (1 + relative_strength))
    result.loc[avg_loss.eq(0) & avg_gain.gt(0), "rsi_14"] = 100
    result.loc[avg_gain.eq(0) & avg_loss.gt(0), "rsi_14"] = 0

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    result["macd"] = ema_12 - ema_26
    result["macd_signal"] = result["macd"].ewm(span=9, adjust=False).mean()
    result["macd_histogram"] = result["macd"] - result["macd_signal"]

    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            result["high"] - result["low"],
            (result["high"] - previous_close).abs(),
            (result["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result["atr_14"] = true_range.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    return result


def detect_latest_patterns(frame: pd.DataFrame) -> list[str]:
    """Detect selected candle formations; patterns are observations, not forecasts."""
    if len(frame) < 2:
        return ["Not enough candles to inspect"]

    latest = frame.iloc[-1]
    previous = frame.iloc[-2]
    body = abs(latest["close"] - latest["open"])
    candle_range = max(latest["high"] - latest["low"], 1e-12)
    upper_wick = latest["high"] - max(latest["open"], latest["close"])
    lower_wick = min(latest["open"], latest["close"]) - latest["low"]
    body_ratio = body / candle_range
    patterns: list[str] = []

    if body_ratio <= 0.10:
        patterns.append("Doji (indecision)")
    elif body_ratio <= 0.30 and upper_wick >= 2 * body and lower_wick >= 2 * body:
        patterns.append("Spinning top (indecision)")

    if body_ratio <= 0.35 and lower_wick >= 2 * max(body, 1e-12) and upper_wick <= candle_range * 0.25:
        patterns.append("Hammer-like candle (context required)")
    if body_ratio <= 0.35 and upper_wick >= 2 * max(body, 1e-12) and lower_wick <= candle_range * 0.25:
        patterns.append("Shooting-star-like candle (context required)")

    previous_bearish = previous["close"] < previous["open"]
    previous_bullish = previous["close"] > previous["open"]
    latest_bullish = latest["close"] > latest["open"]
    latest_bearish = latest["close"] < latest["open"]

    if previous_bearish and latest_bullish:
        if latest["open"] <= previous["close"] and latest["close"] >= previous["open"]:
            patterns.append("Bullish engulfing")
        elif latest["open"] < previous["close"] and latest["close"] > (
            previous["open"] + previous["close"]
        ) / 2:
            patterns.append("Piercing-line-like pattern")

    if previous_bullish and latest_bearish:
        if latest["open"] >= previous["close"] and latest["close"] <= previous["open"]:
            patterns.append("Bearish engulfing")
        elif latest["open"] > previous["close"] and latest["close"] < (
            previous["open"] + previous["close"]
        ) / 2:
            patterns.append("Dark-cloud-cover-like pattern")

    if (
        latest["high"] < previous["high"]
        and latest["low"] > previous["low"]
    ):
        patterns.append("Inside bar")
    elif (
        latest["high"] > previous["high"]
        and latest["low"] < previous["low"]
    ):
        patterns.append("Outside bar")

    if len(frame) >= 3:
        first, middle, last = frame.iloc[-3], frame.iloc[-2], frame.iloc[-1]
        first_body = abs(first["close"] - first["open"])
        middle_body = abs(middle["close"] - middle["open"])
        last_body = abs(last["close"] - last["open"])
        middle_range = max(middle["high"] - middle["low"], 1e-12)

        if (
            first["close"] < first["open"]
            and middle_body / middle_range < 0.35
            and last["close"] > last["open"]
            and last["close"] > (first["open"] + first["close"]) / 2
            and last_body > first_body * 0.5
        ):
            patterns.append("Morning-star-like three-candle pattern")

        if (
            first["close"] > first["open"]
            and middle_body / middle_range < 0.35
            and last["close"] < last["open"]
            and last["close"] < (first["open"] + first["close"]) / 2
            and last_body > first_body * 0.5
        ):
            patterns.append("Evening-star-like three-candle pattern")

        three = frame.iloc[-3:]
        bodies = (three["close"] - three["open"]).to_numpy()
        if np.all(bodies > 0) and np.all(np.diff(three["close"].to_numpy()) > 0):
            patterns.append("Three advancing bullish candles")
        if np.all(bodies < 0) and np.all(np.diff(three["close"].to_numpy()) < 0):
            patterns.append("Three declining bearish candles")

    return patterns or ["No listed pattern detected"]


def educational_assessment(frame: pd.DataFrame) -> dict:
    """Summarise indicator evidence; this is not a trade instruction or probability."""
    data = add_indicators(frame)
    latest = data.iloc[-1]
    score = 0
    evidence: list[str] = []
    cautions: list[str] = []

    if pd.notna(latest["sma_20"]) and pd.notna(latest["sma_50"]):
        if latest["sma_20"] > latest["sma_50"]:
            score += 1
            evidence.append("SMA 20 is above SMA 50.")
        elif latest["sma_20"] < latest["sma_50"]:
            score -= 1
            evidence.append("SMA 20 is below SMA 50.")

    if pd.notna(latest["rsi_14"]):
        if latest["rsi_14"] > 55:
            score += 1
            evidence.append("RSI is above 55, showing positive recent momentum.")
        elif latest["rsi_14"] < 45:
            score -= 1
            evidence.append("RSI is below 45, showing negative recent momentum.")
        else:
            cautions.append("RSI is in the middle zone; momentum is not decisive.")

    if pd.notna(latest["macd"]) and pd.notna(latest["macd_signal"]):
        if latest["macd"] > latest["macd_signal"]:
            score += 1
            evidence.append("MACD is above its signal line.")
        elif latest["macd"] < latest["macd_signal"]:
            score -= 1
            evidence.append("MACD is below its signal line.")

    if score >= 2:
        label = "Bullish evidence"
    elif score <= -2:
        label = "Bearish evidence"
    else:
        label = "Mixed / unclear evidence"

    if not evidence:
        cautions.append("Not enough indicator history to form an assessment.")
    cautions.append(
        "This simple score is not statistically calibrated and does not predict future prices."
    )

    return {
        "label": label,
        "score": score,
        "evidence": evidence,
        "cautions": cautions,
        "patterns": detect_latest_patterns(frame),
        "indicators": data,
    }


def compare_timeframes(frames: dict[str, pd.DataFrame]) -> dict:
    """Compare independent timeframe assessments without treating agreement as certainty."""
    reports = {name: educational_assessment(frame) for name, frame in frames.items()}
    labels = [report["label"] for report in reports.values()]
    bullish = labels.count("Bullish evidence")
    bearish = labels.count("Bearish evidence")
    mixed = labels.count("Mixed / unclear evidence")

    if bullish and bearish:
        overall = "Timeframes disagree"
    elif bullish and not bearish and not mixed:
        overall = "Bullish evidence aligned"
    elif bearish and not bullish and not mixed:
        overall = "Bearish evidence aligned"
    else:
        overall = "Mixed timeframe picture"

    return {
        "overall": overall,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "mixed_count": mixed,
        "reports": reports,
        "note": "Timeframe agreement is not proof of predictive power; each timeframe uses the same simple, uncalibrated indicators.",
    }
