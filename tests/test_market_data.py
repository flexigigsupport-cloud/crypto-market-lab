import pandas as pd
import pytest
import market_data

class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): pass
    def json(self): return self.payload

def test_history_rejects_bad_parameters():
    with pytest.raises(ValueError):
        market_data.fetch_candles_history("DOGE-USD", "1h", 500)
    with pytest.raises(ValueError):
        market_data.fetch_candles_history("BTC-USD", "1h", 50)

def test_history_paginates_and_deduplicates(monkeypatch):
    calls = []
    def fake_get(url, params, headers, timeout):
        calls.append(params)
        end = pd.Timestamp(params["end"])
        stamps = pd.date_range(end=end.floor("h") - pd.Timedelta(hours=1), periods=3, freq="h", tz="UTC")
        payload = [[int(ts.timestamp()), 99, 102, 100, 101, 10] for ts in stamps[::-1]]
        return FakeResponse(payload)
    monkeypatch.setattr(market_data.requests, "get", fake_get)
    monkeypatch.setattr(market_data.time, "sleep", lambda _: None)
    result = market_data.fetch_candles_history("BTC-USD", "1h", 100)
    assert len(calls) > 1
    assert result.index.is_monotonic_increasing
    assert not result.index.has_duplicates
