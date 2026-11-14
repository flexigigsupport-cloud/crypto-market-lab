"""Read-only Coinbase Exchange public candle-data client."""

from __future__ import annotations

import requests
import pandas as pd

BASE_URL = "https://api.exchange.coinbase.com"
TIMEFRAMES = {
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "6h": 21600,
    "1d": 86400,
}
PRODUCTS = ["BTC-USD", "ETH-USD", "SOL-USD"]

COLUMNS = ["timestamp", "low", "high", "open", "close", "volume"]


class MarketDataError(RuntimeError):
    """Raised when public market data cannot be retrieved or parsed."""


def fetch_candles(product_id: str, timeframe: str, limit: int = 250) -> pd.DataFrame:
    """Fetch public OHLCV candles. No account or trading credentials are used."""
    if product_id not in PRODUCTS:
        raise ValueError(f"Unsupported product: {product_id}")
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    if not 30 <= limit <= 300:
        raise ValueError("limit must be between 30 and 300")

    url = f"{BASE_URL}/products/{product_id}/candles"
    params = {"granularity": TIMEFRAMES[timeframe]}
    headers = {"Accept": "application/json", "User-Agent": "CryptoMarketLab/0.1"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise MarketDataError(f"Could not retrieve market candles: {exc}") from exc

    if not isinstance(payload, list) or not payload:
        raise MarketDataError("The data provider returned no candle data.")

    frame = pd.DataFrame(payload, columns=COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
    for column in COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = (
        frame.dropna()
        .drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
        .tail(limit)
        .set_index("timestamp")
    )
    if frame.empty:
        raise MarketDataError("No valid candles were returned.")
    return frame
