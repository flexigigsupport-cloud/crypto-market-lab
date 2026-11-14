"""Read-only Coinbase Exchange public candle-data client."""
from __future__ import annotations
import time
import requests
import pandas as pd

BASE_URL = "https://api.exchange.coinbase.com"
TIMEFRAMES = {"5m": 300, "15m": 900, "1h": 3600, "6h": 21600, "1d": 86400}
PRODUCTS = ["BTC-USD", "ETH-USD", "SOL-USD"]
COLUMNS = ["timestamp", "low", "high", "open", "close", "volume"]
MAX_CANDLES_PER_REQUEST = 300


class MarketDataError(RuntimeError):
    pass


def _request_candle_batch(product_id, seconds, start=None, end=None):
    params = {"granularity": seconds}
    if start is not None:
        params["start"] = start.isoformat()
    if end is not None:
        params["end"] = end.isoformat()
    try:
        response = requests.get(
            f"{BASE_URL}/products/{product_id}/candles", params=params,
            headers={"Accept": "application/json", "User-Agent": "CryptoMarketLab/0.3"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise MarketDataError(f"Could not retrieve market candles: {exc}") from exc
    if not isinstance(payload, list):
        raise MarketDataError("Unexpected candle response.")
    if not payload:
        return pd.DataFrame(columns=COLUMNS[1:], index=pd.DatetimeIndex([], name="timestamp"))
    try:
        frame = pd.DataFrame(payload, columns=COLUMNS)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
        for col in COLUMNS[1:]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        return frame.dropna().drop_duplicates("timestamp").set_index("timestamp").sort_index()
    except (TypeError, ValueError, KeyError) as exc:
        raise MarketDataError("Unexpected candle format.") from exc


def _validate_frame(frame, seconds):
    frame = frame.sort_index()
    frame = frame.loc[frame.index + pd.to_timedelta(seconds, unit="s") <= pd.Timestamp.now(tz="UTC")]
    if frame.empty:
        raise MarketDataError("No completed valid candles were returned.")
    prices = frame[["low", "high", "open", "close"]]
    if (prices <= 0).any().any():
        raise MarketDataError("Provider returned non-positive prices.")
    if (frame["high"] < frame[["open", "close", "low"]].max(axis=1)).any():
        raise MarketDataError("Provider returned invalid candle highs.")
    if (frame["low"] > frame[["open", "close", "high"]].min(axis=1)).any():
        raise MarketDataError("Provider returned invalid candle lows.")
    return frame


def fetch_candles(product_id, timeframe, limit=250):
    """Fetch up to 300 latest completed public candles."""
    if product_id not in PRODUCTS:
        raise ValueError(f"Unsupported product: {product_id}")
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    if not 30 <= limit <= 300:
        raise ValueError("limit must be between 30 and 300")
    seconds = TIMEFRAMES[timeframe]
    return _validate_frame(_request_candle_batch(product_id, seconds), seconds).tail(limit)


def fetch_candles_history(product_id, timeframe, limit=1500):
    """Fetch up to 5,000 candles using adjacent, bounded historical requests."""
    if product_id not in PRODUCTS:
        raise ValueError(f"Unsupported product: {product_id}")
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    if not 100 <= limit <= 5000:
        raise ValueError("Historical limit must be between 100 and 5000 candles.")
    seconds = TIMEFRAMES[timeframe]
    cursor_end = pd.Timestamp.now(tz="UTC").floor("s")
    batches = []
    max_requests = (limit + MAX_CANDLES_PER_REQUEST - 1) // MAX_CANDLES_PER_REQUEST + 2
    for page in range(max_requests):
        start = cursor_end - pd.to_timedelta(seconds * MAX_CANDLES_PER_REQUEST, unit="s")
        batch = _request_candle_batch(product_id, seconds, start, cursor_end)
        if not batch.empty:
            batches.append(batch)
        combined_count = sum(len(item) for item in batches)
        if combined_count >= limit:
            break
        if batch.empty:
            cursor_end = start
        else:
            cursor_end = batch.index.min() - pd.Timedelta(seconds=1)
        if page + 1 < max_requests:
            time.sleep(0.15)
    if not batches:
        raise MarketDataError("No historical candles were returned.")
    combined = pd.concat(batches)
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    return _validate_frame(combined, seconds).tail(limit)
