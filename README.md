# Crypto Market Lab

A private-use **educational cryptocurrency market research dashboard**. It retrieves public market candles, calculates common technical indicators, recognises candlestick formations, and compares evidence across timeframes.

> **Research and simulation only.** This project does not connect to exchange accounts, place orders, or provide personalised financial advice. Bullish/bearish/mixed assessments are experimental summaries of historical price data, not instructions to trade or promises about future performance.

## Current features

- Public BTC-USD, ETH-USD and SOL-USD candles from Coinbase Exchange.
- Timeframes: 5 minutes, 15 minutes, 1 hour, 6 hours and 1 day.
- SMA 20 / SMA 50, RSI 14, MACD and ATR 14.
- Candlestick observations: doji, spinning top, hammer-like, shooting-star-like, bullish/bearish engulfing, piercing-line-like, dark-cloud-cover-like, inside/outside bars, and selected three-candle formations.
- A transparent educational evidence score with supporting observations and cautions.
- Multi-timeframe comparison that explicitly identifies disagreement.
- Unit tests for indicator output, pattern detection and timeframe comparison.

Pattern names are approximate rule-based detections. They do not account for every market context and are not validated trading signals.

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

The app uses Coinbase Exchange's public candles endpoint:
`https://api.exchange.coinbase.com/products/{product_id}/candles`

The application filters out the currently forming candle before analysis. Public endpoints can have rate limits, temporary outages, and product/region availability differences. The dashboard refreshes on request; it is not a tick-by-tick WebSocket terminal.

## Roadmap

1. Validate indicator calculations and market-data handling.
2. Expand and test candlestick pattern recognition.
3. Compare multiple timeframes.
4. Add more strategy research modules and market-regime descriptions.
5. Add historical backtesting with fees, spread, slippage, and out-of-sample evaluation.
6. Add paper-only simulation and performance reporting.
7. Evaluate additional read-only market-data providers.

## Safety and security

- Never commit API secrets, passwords, exchange credentials, or private keys.
- Do not add live order execution or trading-account integration.
- Treat every assessment as uncertain research output. A strategy that appears successful on past data may fail on new data.
