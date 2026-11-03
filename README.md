# Mahim Quotex AI Signal Dashboard

A mobile-friendly FastAPI dashboard and indicator-analysis starter.

## Run locally
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000` for the dashboard and `/docs` for API documentation.

## Deploy to Render
1. Upload the contents of this folder to a new GitHub repository.
2. In Render, select New + → Blueprint and connect the repository.
3. Deploy using `render.yaml`.
4. Open your Render service URL for the dashboard. Add `/docs` for API docs.

## Data limitations
- Demo Analysis uses generated illustrative candles. It is NOT live market data.
- For API analysis, paste at least 55 genuine chronological OHLC candles.
- OTC analysis intentionally returns an unavailable response until a verified Quotex OTC feed is connected. Forex prices are not a substitute for OTC prices.
- The score is a rule-based indicator score, not the probability of winning. No signal guarantees profit.
- Render free services may sleep and have usage limits.
