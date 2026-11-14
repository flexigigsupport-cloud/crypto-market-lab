# Crypto Market Lab

A private-use **educational cryptocurrency market research dashboard**. It retrieves public market candles, calculates common technical indicators, recognises a small set of candlestick patterns, and compares evidence across timeframes.

> **Research and simulation only.** This project does not connect to brokerage/exchange accounts, place orders, or provide personalised financial advice. Bullish/bearish/neutral assessments are experimental summaries of historical price data, not instructions to trade or promises of future performance.

## Current MVP

- Public BTC-USD, ETH-USD and SOL-USD candle data from Coinbase Exchange's public market-data API.
- Timeframes: 5 minutes, 15 minutes, 1 hour, 6 hours and 1 day.
- SMA 20 / SMA 50, RSI 14 and MACD.
- Basic doji, hammer, shooting-star, bullish-engulfing and bearish-engulfing pattern detection.
- A transparent educational evidence score with supporting and conflicting observations.
- Streamlit dashboard with a price chart and indicator view.

The dashboard refreshes data when requested. It is not a tick-by-tick WebSocket terminal.

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

Then open the local URL printed by Streamlit.

## Data source

The app uses Coinbase Exchange's public candles endpoint:
`https://api.exchange.coinbase.com/products/{product_id}/candles`

Public endpoints can have rate limits, temporary outages, and product/region availability differences. The app makes no authenticated account connection.

## Roadmap

1. Validate data handling and indicator calculations with tests.
2. Add more candlestick patterns and clearly explain each detection.
3. Add multi-timeframe comparison and configurable strategy modules.
4. Build historical backtesting with fees, spread, slippage, and out-of-sample evaluation.
5. Add paper-only simulation and performance reporting.
6. Evaluate additional read-only market-data providers.

## Safety and security

- Never commit API secrets, passwords, exchange credentials, or private keys.
- Do not add live order execution or trading-account integration.
- Treat all assessments as uncertain research outputs. A strategy that looks good on past data may fail on new data.
