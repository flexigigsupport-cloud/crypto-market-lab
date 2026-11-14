# Crypto Market Lab

A personal **educational cryptocurrency market research dashboard**. It retrieves public market candles, calculates technical indicators, recognises candlestick formations, compares timeframes and runs historical paper simulations.

> **Research and simulation only.** This project does not connect to exchange accounts, place orders, or provide personalised financial advice. Assessments and historical results are uncertain research outputs, not instructions to trade or promises about future performance.

## Current features

- Public BTC-USD, ETH-USD and SOL-USD candles from Coinbase Exchange.
- Timeframes: 5 minutes, 15 minutes, 1 hour, 6 hours and 1 day.
- SMA 20 / SMA 50, RSI 14, MACD and ATR 14.
- Rule-based observations for common single- and multi-candle patterns.
- Transparent educational evidence score and multi-timeframe comparison.
- Historical paper backtest for two simple research rules: SMA trend filter and RSI momentum filter.
- Assumed fees and slippage are deducted on position changes.
- Equity curve, buy-and-hold comparison, maximum drawdown, exposure and position-change count.
- Unit tests for indicators, patterns, timeframe comparison and backtest validation.

## Backtest methodology and limitations

- A signal calculated using candle t is applied to candle t+1's return, avoiding same-candle lookahead.
- Simulated exposure is long/flat; no orders are sent anywhere.
- The simplified model deducts the configured fee and slippage assumptions on each unit of position turnover.
- It does not model order-book depth, liquidity, partial fills, funding, taxes, outages or all real-world costs.
- Results depend heavily on the selected asset, timeframe, date range and assumptions.
- The current dashboard sample is small and is not out-of-sample validation. No parameters have been optimised or validated for predictive power.
- Historical results do not forecast future performance. Avoid selecting a rule merely because it looks best on this sample.

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
4. Add historical paper backtesting with explicit cost assumptions.
5. Improve validation with longer historical datasets and chronological out-of-sample testing.
6. Add more read-only market-data providers and market-regime research.

## Safety and security

- Never commit API secrets, passwords, exchange credentials or private keys.
- Do not add live order execution or trading-account integration.
- Treat every assessment and simulation as uncertain research output.
