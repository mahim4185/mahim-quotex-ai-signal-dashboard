import os, json, time
from datetime import datetime, timezone
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Mahim Quotex AI Signal Dashboard", version="2.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

SYMBOLS = {
    "EUR/USD": "EUR/USD",
    "GBP/USD": "GBP/USD",
    "USD/JPY": "USD/JPY",
    "AUD/USD": "AUD/USD",
    "USD/CAD": "USD/CAD",
    "USD/CHF": "USD/CHF",
    "NZD/USD": "NZD/USD",
}

class Account(BaseModel):
    account_id: str

@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/api/status")
def status():
    return {
        "provider_configured": bool(os.getenv("TWELVE_DATA_API_KEY")),
        "provider": "Twelve Data" if os.getenv("TWELVE_DATA_API_KEY") else None,
        "otc_available": False,
        "message": "Live Forex feed ready" if os.getenv("TWELVE_DATA_API_KEY") else "Live data API key is not configured. Demo signals are illustrative only."
    }

@app.post("/api/account")
def save_account(data: Account):
    account_id = data.account_id.strip()
    if not account_id or len(account_id) > 80:
        raise HTTPException(400, "Enter a valid account ID.")
    # This stores only a label/ID. It does not log in to Quotex or access account data.
    with open("/tmp/mahim_account.json", "w", encoding="utf-8") as f:
        json.dump({"account_id": account_id}, f)
    return {"saved": True, "account_id": account_id,
            "note": "ID saved as a label only; it is not connected to Quotex."}

@app.get("/api/account")
def get_account():
    try:
        with open("/tmp/mahim_account.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"account_id": ""}

def ema(values, period):
    alpha = 2 / (period + 1)
    result = values[0]
    for v in values[1:]:
        result = alpha * v + (1-alpha) * result
    return result

@app.get("/api/signal")
async def signal(symbol: str = "EUR/USD", market: str = "forex", interval: str = "1min"):
    market = market.lower()
    if market == "otc":
        return {"available": False, "market": "OTC", "symbol": symbol,
                "signal": "WAIT", "reason": "No verified Quotex OTC feed is configured. No fabricated OTC signal will be shown.",
                "source": "none", "timestamp": datetime.now(timezone.utc).isoformat()}
    if symbol not in SYMBOLS:
        raise HTTPException(400, "Unsupported symbol.")
    key = os.getenv("TWELVE_DATA_API_KEY")
    if not key:
        return {"available": False, "market": "Forex", "symbol": symbol,
                "signal": "WAIT", "reason": "Live data source is not configured. Add TWELVE_DATA_API_KEY in Render environment variables.",
                "source": "none", "timestamp": datetime.now(timezone.utc).isoformat()}
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": symbol, "interval": interval, "outputsize": 100, "apikey": key}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            data = r.json()
        if "values" not in data:
            return {"available": False, "market": "Forex", "symbol": symbol,
                    "signal": "WAIT", "reason": data.get("message", "Market data unavailable."),
                    "source": "Twelve Data", "timestamp": datetime.now(timezone.utc).isoformat()}
        closes = [float(x["close"]) for x in reversed(data["values"]) if x.get("close")]
        if len(closes) < 55:
            raise ValueError("Not enough candles")
        fast, slow = ema(closes[-50:], 9), ema(closes[-50:], 21)
        momentum = closes[-1] - closes[-6]
        if fast > slow and momentum > 0:
            sig, reason = "CALL", "EMA 9 is above EMA 21 and recent momentum is positive."
        elif fast < slow and momentum < 0:
            sig, reason = "PUT", "EMA 9 is below EMA 21 and recent momentum is negative."
        else:
            sig, reason = "WAIT", "Trend and momentum do not agree."
        return {"available": True, "market": "Forex", "symbol": symbol, "signal": sig,
                "reason": reason, "source": "Twelve Data", "last_price": closes[-1],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "warning": "Analysis only; not a guaranteed prediction or financial advice."}
    except Exception as e:
        return {"available": False, "market": "Forex", "symbol": symbol, "signal": "WAIT",
                "reason": "Could not retrieve enough reliable live candles: " + str(e),
                "source": "Twelve Data", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/health")
def health():
    return {"ok": True}
