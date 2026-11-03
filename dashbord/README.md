# Mahim Quotex AI Signal Dashboard V4

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Open http://127.0.0.1:8000

## Data source
Uses Biquote public OHLC endpoint documented at https://biquote.io/docs/:
`GET https://biquote.io/api/{symbol}/ohlc?interval=1m&limit=250`

Only completed candles are used. If the provider fails or returns too few candles, the app returns an error and does not generate a fake signal.

## Important limitations
- Biquote is an external market-data provider, not Quotex's own price feed.
- OTC symbols are not supported.
- CALL/PUT/WAIT is a basic educational indicator rule, not a validated trading strategy.
- Strength score is NOT probability of winning.
- No automated trading, broker login, or financial advice.
- Manually label outcomes only after a pre-defined expiry period; results can be biased if timing/expiry is inconsistent.
- Free Render instances may sleep. SQLite data may be lost on redeploy/restart without persistent storage.

## Before any real-money use
Run a pre-defined demo test across multiple market sessions and at least 200 signals, record exact entry/expiry rules, include payout/breakeven calculations, and evaluate out-of-sample results. Even a positive backtest does not guarantee future performance.
