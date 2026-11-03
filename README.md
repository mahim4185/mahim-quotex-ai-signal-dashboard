# Mahim Quotex AI Signal Dashboard v2

A mobile-friendly, indicator-based analysis dashboard. It is **not** an official Quotex product and does not connect to Quotex accounts or place trades.

## Included
- FastAPI backend and responsive Bangla-friendly dashboard.
- Timeframe selector: 1m, 5m, 15m, 30m, 1h.
- EMA 9/21/50, RSI 14 and MACD rule-based analysis.
- CALL / PUT / WAIT output with transparent reasons.
- SQLite signal history and manually recorded WIN / LOSS / DRAW outcomes.
- Basic stats from manually recorded outcomes.
- Demo sample mode and user-supplied candle JSON mode.
- OTC disabled until a verified, authorized OTC candle feed is available.

## Important limitations
- Demo mode generates illustrative random candles. It is only for checking that the interface works. It is not market data.
- No live Quotex candle feed is included. No credentials, browser scraping, WebSocket interception or auto-click trading are used.
- OTC candles cannot be substituted with Forex candles.
- “Signal strength” is a rule-based indicator score, **not** the probability of winning.
- A recorded win rate is only based on outcomes manually marked in this dashboard. It is not a verified backtest.
- No signal guarantees profit. Binary options are high risk; use a demo account and never risk money you cannot afford to lose.

## Run locally
Python 3.10+ recommended.

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Open `http://127.0.0.1:8000`.

## Input candle format
Provide at least 55 candles in chronological order (oldest first), each with:
`time`, `open`, `high`, `low`, `close`. Optional `volume`.

Example:
```json
[
  {"time":"2026-11-03T09:00:00Z","open":1.1500,"high":1.1510,"low":1.1490,"close":1.1505,"volume":0}
]
```
Use genuine OHLC data from a source you are authorized to access. Ensure the timeframe and symbol match the selected settings.

## Deploy on Render
1. Upload all files and the `static` folder to a GitHub repository.
2. In Render, create a new **Blueprint** and select the repository containing `render.yaml`, or create a Web Service with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Free hosting may sleep when idle. Local SQLite storage may not persist across some redeploys or ephemeral disks; use a persistent disk/database for long-term history.

## API endpoints
- `GET /api/health`
- `POST /api/analyze`
- `GET /api/history?limit=30`
- `GET /api/stats`
- `POST /api/outcome/{signal_id}?outcome=WIN|LOSS|DRAW`

## Next development stage
Connect only a verified and permitted candle-data provider through a separate adapter. Before adding ML, collect a sufficiently large, clean, timestamped dataset and evaluate with out-of-sample walk-forward tests. Do not claim a win rate until independently measured.
