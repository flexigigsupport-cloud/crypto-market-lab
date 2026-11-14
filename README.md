# Crypto Market Lab

A personal **educational cryptocurrency market research dashboard** using public market data, technical indicators, candlestick observations, timeframe comparisons and historical paper simulations.

> **Research and simulation only.** No exchange accounts, order execution or personalised financial advice. Assessments and historical results are uncertain and are not trading instructions or promises.

## Features

- Public BTC-USD, ETH-USD and SOL-USD candles from Coinbase Exchange.
- 5m, 15m, 1h, 6h and 1d timeframes.
- SMA 20/50, RSI 14, MACD and ATR 14.
- Rule-based candlestick observations and multi-timeframe comparison.
- Historical long/flat paper simulations for an SMA trend filter and RSI momentum filter.
- Assumed fees and slippage deducted on position turnover.
- Equity curve, buy-and-hold comparison, maximum drawdown, exposure and position-change metrics.
- Chronological holdout evaluation: earlier candles warm up indicators; only the later segment contributes to reported performance.

## Backtest methodology and limitations

- A signal calculated at candle t is applied to candle t+1's return.
- The final chronological portion is held out from reported metrics; the default is 30%, configurable from 10% to 50%.
- The holdout boundary is treated as a fresh paper portfolio, with entry cost charged when exposed.
- The model is long/flat and simplified. It does not model order-book depth, liquidity, partial fills, funding, taxes or every real-world cost.
- A single holdout is not repeated walk-forward validation. The currently available data request is capped at 300 candles, so conclusions from it are especially limited.
- A rule can look successful by chance or overfitting. Do not optimise repeatedly against the holdout and then treat it as independent evidence.
- Historical results do not predict future performance.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run tests:

```bash
pytest -q
```

## Data source

Coinbase Exchange public candles endpoint:
`https://api.exchange.coinbase.com/products/{product_id}/candles`

The app excludes the currently forming candle. Public endpoints may have rate limits, outages and regional/product availability differences. Refresh is user-triggered, not tick-by-tick.

## Security

- Never commit passwords, API secrets, exchange credentials or private keys.
- Do not add live order execution or trading-account integration.
