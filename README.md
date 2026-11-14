# Crypto Market Lab

Personal, read-only educational cryptocurrency market research dashboard.

**Safety:** No exchange account connection, deposits, private credentials, order placement or automated execution. All assessments and simulations are uncertain research outputs, not trading recommendations or promises.

## Features
- Public BTC-USD, ETH-USD and SOL-USD candles from Coinbase Exchange.
- 5m, 15m, 1h, 6h and 1d timeframes.
- Paginated retrieval of up to 5,000 historical candles (provider responses capped at 300 per request).
- SMA 20/50, RSI 14, MACD and ATR 14; rule-based candlestick observations.
- Multi-timeframe evidence comparison.
- Fixed SMA and RSI long/flat paper simulations with assumed fees and slippage.
- Single chronological holdout and sequential walk-forward evaluation.

## Method and limitations
- Signals calculated at candle t apply to candle t+1 returns.
- Walk-forward testing uses an initial history segment followed by later sequential test folds. Rules are fixed; no tuning occurs on the test folds.
- Simplified model: no order-book depth, liquidity, partial fills, funding, taxes or every real-world cost.
- Data availability and API rate limits can affect historical coverage. Check the displayed date range.
- Walk-forward validation does not prove predictive power. Past results do not forecast future performance.

## Run locally
Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local address printed by Streamlit, normally http://localhost:8501.

Run tests with `pytest -q`. GitHub Actions runs pytest on pushes and pull requests.

## Data source
Coinbase Exchange public candles endpoint: https://api.exchange.coinbase.com/products/{product_id}/candles

Historical requests are paginated in windows no larger than 300 candles. The current unfinished candle is excluded.

## Security
The repository is public. Never commit passwords, API secrets, exchange credentials or private keys. This project intentionally remains read-only and paper-simulation-only.
