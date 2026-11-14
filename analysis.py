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


def strategy_consensus_research(frame: pd.DataFrame) -> dict:
    """Combine distinct descriptive research lenses; never emits trade instructions."""
    data = add_indicators(frame)
    if len(data) < 60:
        raise ValueError("At least 60 completed candles are required for strategy-consensus research.")

    latest = data.iloc[-1]
    previous = data.iloc[-2]
    lenses: list[dict[str, str]] = []

    # Trend lens: moving-average structure and recent close location.
    if pd.notna(latest["sma_20"]) and pd.notna(latest["sma_50"]):
        if latest["sma_20"] > latest["sma_50"] and latest["close"] > latest["sma_20"]:
            bias, reason = "Bullish", "Close is above SMA 20 and SMA 20 is above SMA 50."
        elif latest["sma_20"] < latest["sma_50"] and latest["close"] < latest["sma_20"]:
            bias, reason = "Bearish", "Close is below SMA 20 and SMA 20 is below SMA 50."
        else:
            bias, reason = "Neutral", "Moving averages and close do not form a fully aligned trend."
        lenses.append({"strategy": "Trend structure", "bias": bias, "reason": reason})

    # Momentum lens.
    rsi = latest["rsi_14"]
    if pd.notna(rsi):
        if rsi >= 55:
            bias, reason = "Bullish", f"RSI is {rsi:.1f}, above the neutral momentum band."
        elif rsi <= 45:
            bias, reason = "Bearish", f"RSI is {rsi:.1f}, below the neutral momentum band."
        else:
            bias, reason = "Neutral", f"RSI is {rsi:.1f}, within the middle momentum band."
        lenses.append({"strategy": "RSI momentum", "bias": bias, "reason": reason})

    # MACD lens.
    if pd.notna(latest["macd_histogram"]):
        if latest["macd_histogram"] > 0 and latest["macd_histogram"] >= previous["macd_histogram"]:
            bias, reason = "Bullish", "MACD histogram is positive and has not contracted on the latest candle."
        elif latest["macd_histogram"] < 0 and latest["macd_histogram"] <= previous["macd_histogram"]:
            bias, reason = "Bearish", "MACD histogram is negative and has not improved on the latest candle."
        else:
            bias, reason = "Neutral", "MACD histogram is mixed or changing direction."
        lenses.append({"strategy": "MACD momentum", "bias": bias, "reason": reason})

    # Candle lens: only directional named patterns are counted.
    patterns = detect_latest_patterns(frame)
    bullish_terms = ("Bullish engulfing", "Piercing-line", "Morning-star", "Three advancing")
    bearish_terms = ("Bearish engulfing", "Dark-cloud", "Evening-star", "Three declining")
    bullish_pattern = any(any(term in pattern for term in bullish_terms) for pattern in patterns)
    bearish_pattern = any(any(term in pattern for term in bearish_terms) for pattern in patterns)
    if bullish_pattern and not bearish_pattern:
        candle_bias = "Bullish"
        candle_reason = "A bullish reversal/continuation formation was detected; context still matters."
    elif bearish_pattern and not bullish_pattern:
        candle_bias = "Bearish"
        candle_reason = "A bearish reversal/continuation formation was detected; context still matters."
    else:
        candle_bias = "Neutral"
        candle_reason = "No unambiguous directional pattern was detected in the latest candle sequence."
    lenses.append({"strategy": "Candlestick structure", "bias": candle_bias, "reason": candle_reason})

    # Volume lens: relative activity only, not direction by itself.
    if "volume" in data.columns and data["volume"].notna().sum() >= 20:
        volume_median = data["volume"].tail(20).median()
        if pd.notna(volume_median) and volume_median > 0:
            volume_ratio = latest["volume"] / volume_median
            if volume_ratio >= 1.5 and latest["close"] > latest["open"]:
                bias, reason = "Bullish", f"Latest up-candle volume is {volume_ratio:.2f}× its 20-candle median."
            elif volume_ratio >= 1.5 and latest["close"] < latest["open"]:
                bias, reason = "Bearish", f"Latest down-candle volume is {volume_ratio:.2f}× its 20-candle median."
            else:
                bias, reason = "Neutral", f"Latest volume is {volume_ratio:.2f}× its 20-candle median; no strong directional confirmation."
            lenses.append({"strategy": "Relative volume", "bias": bias, "reason": reason})

    # Volatility is deliberately a context lens, not a directional vote.
    atr = latest["atr_14"]
    if pd.notna(atr) and latest["close"] != 0:
        atr_pct = float(atr / latest["close"] * 100)
        atr_median = data["atr_14"].tail(100).median()
        if pd.notna(atr_median) and atr_median > 0:
            regime = "elevated" if atr > atr_median * 1.25 else "compressed" if atr < atr_median * 0.75 else "typical"
        else:
            regime = "not yet classified"
        lenses.append({
            "strategy": "Volatility context",
            "bias": "Context",
            "reason": f"ATR(14) is {atr_pct:.2f}% of close; recent volatility is {regime} versus its trailing sample.",
        })

    directional = [item["bias"] for item in lenses if item["bias"] in ("Bullish", "Bearish", "Neutral")]
    bullish = directional.count("Bullish")
    bearish = directional.count("Bearish")
    neutral = directional.count("Neutral")
    if bullish > bearish and bullish >= 2:
        overall = "Bullish evidence leads"
    elif bearish > bullish and bearish >= 2:
        overall = "Bearish evidence leads"
    else:
        overall = "Mixed / no clear consensus"

    # A rolling historical range is context only, not a projected target.
    history = data.tail(50)
    range_context = {
        "lookback_candles": len(history),
        "observed_low": float(history["low"].min()),
        "observed_high": float(history["high"].max()),
        "latest_close": float(latest["close"]),
    }
    return {
        "overall": overall,
        "bullish_lenses": bullish,
        "bearish_lenses": bearish,
        "neutral_lenses": neutral,
        "lenses": lenses,
        "patterns": patterns,
        "historical_range_context": range_context,
        "note": "Lens counts are descriptive, not probabilities. The lenses are correlated and are not independently validated. The 50-candle high/low are historical observations, not entry, stop or take-profit levels.",
    }
