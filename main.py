from __future__ import annotations
import json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "signals.db"

app = FastAPI(title="Mahim Quotex AI Signal Dashboard", version="2.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = 0

class AnalyzeRequest(BaseModel):
    symbol: str = Field(default="EURUSD", min_length=2, max_length=30)
    market: Literal["FOREX", "OTC"] = "FOREX"
    timeframe: Literal["1m", "5m", "15m", "30m", "1h"] = "1m"
    candles: list[Candle] = Field(min_length=55, max_length=2000)
    source: str = "MANUAL_OR_AUTHORIZED_FEED"

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY, created_at TEXT, symbol TEXT, market TEXT,
            timeframe TEXT, direction TEXT, score INTEGER, reasons TEXT,
            reference_price REAL, source TEXT, outcome TEXT DEFAULT 'PENDING'
        )""")

def ema(values, period):
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1-k))
    return out

def rsi(values, period=14):
    gains, losses = [], []
    for i in range(1, len(values)):
        d = values[i] - values[i-1]
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain*(period-1) + gains[i]) / period
        avg_loss = (avg_loss*(period-1) + losses[i]) / period
    if avg_loss == 0: return 100.0
    return 100 - (100 / (1 + avg_gain/avg_loss))

def analyze(req: AnalyzeRequest):
    candles = req.candles
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    # Basic sanity checks: reject impossible OHLC rows.
    for c in candles:
        if c.high < max(c.open, c.close) or c.low > min(c.open, c.close) or c.high < c.low:
            raise HTTPException(422, "Invalid OHLC candle: high/low do not contain open and close.")
    e9, e21, e50 = ema(closes, 9), ema(closes, 21), ema(closes, 50)
    r = rsi(closes)
    macd_line = ema(closes, 12)[-1] - ema(closes, 26)[-1]
    signal_line = ema([ema(closes, 12)[i] - ema(closes, 26)[i] for i in range(len(closes))], 9)[-1]
    recent_range = sum(highs[-14:]) / 14 - sum(lows[-14:]) / 14
    avg_range = sum((highs[i]-lows[i]) for i in range(-14, 0)) / 14
    score = 0
    reasons = []
    if e9[-1] > e21[-1]:
        score += 1; reasons.append("EMA 9 is above EMA 21 (short-term bullish).")
    else:
        score -= 1; reasons.append("EMA 9 is below EMA 21 (short-term bearish).")
    if e21[-1] > e50[-1]:
        score += 1; reasons.append("EMA 21 is above EMA 50 (trend bullish).")
    else:
        score -= 1; reasons.append("EMA 21 is below EMA 50 (trend bearish).")
    if r >= 55:
        score += 1; reasons.append(f"RSI is {r:.1f}, showing positive momentum.")
    elif r <= 45:
        score -= 1; reasons.append(f"RSI is {r:.1f}, showing negative momentum.")
    else:
        reasons.append(f"RSI is {r:.1f}, in a neutral zone.")
    if macd_line > signal_line:
        score += 1; reasons.append("MACD is above its signal line.")
    else:
        score -= 1; reasons.append("MACD is below its signal line.")
    # Avoid overstating a direction in very low movement / conflicting conditions.
    if score >= 3: direction = "CALL"
    elif score <= -3: direction = "PUT"
    else: direction = "WAIT"
    strength = min(90, 50 + abs(score)*9)
    if direction == "WAIT": strength = max(50, 65 - abs(score)*4)
    latest = closes[-1]
    candle_body = abs(candles[-1].close - candles[-1].open)
    volatility = "HIGH" if avg_range > 0 and (avg_range / max(abs(latest), 1e-9))*10000 > 8 else "NORMAL/LOW"
    if direction == "WAIT":
        reasons.append("Indicators are mixed; waiting is safer than forcing a trade.")
    return {
        "direction": direction,
        "score": score,
        "signal_strength": strength,
        "signal_strength_note": "Rule-based indicator strength only; NOT a win probability.",
        "rsi": round(r, 2),
        "ema9": round(e9[-1], 6), "ema21": round(e21[-1], 6), "ema50": round(e50[-1], 6),
        "macd": round(macd_line, 8), "macd_signal": round(signal_line, 8),
        "volatility": volatility,
        "reference_price": latest,
        "last_candle_time": candles[-1].time,
        "reasons": reasons
    }

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"status":"ok", "version":"2.0.0",
            "live_feed_connected":False,
            "otc_feed_connected":False,
            "message":"Analysis API is ready. No live Quotex feed is connected."}

@app.post("/api/analyze")
def api_analyze(req: AnalyzeRequest):
    if req.market == "OTC":
        raise HTTPException(501, "OTC analysis is disabled until a verified, authorized OTC candle feed is connected. Forex candles are not OTC data.")
    result = analyze(req)
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with db() as con:
        con.execute("""INSERT INTO signals
            (id,created_at,symbol,market,timeframe,direction,score,reasons,reference_price,source)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sid,now,req.symbol,req.market,req.timeframe,result["direction"],result["score"],
             json.dumps(result["reasons"]),result["reference_price"],req.source))
    result.update({"id":sid,"created_at":now,"symbol":req.symbol,"market":req.market,
                   "timeframe":req.timeframe,"source":req.source})
    return result

@app.get("/api/history")
def history(limit: int = 30):
    limit = max(1, min(limit, 100))
    with db() as con:
        rows = con.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

@app.post("/api/outcome/{signal_id}")
def update_outcome(signal_id: str, outcome: Literal["WIN","LOSS","DRAW"]):
    with db() as con:
        cur = con.execute("UPDATE signals SET outcome=? WHERE id=?", (outcome,signal_id))
        if cur.rowcount == 0: raise HTTPException(404,"Signal not found")
    return {"updated":True,"id":signal_id,"outcome":outcome}

@app.get("/api/stats")
def stats():
    with db() as con:
        rows = con.execute("SELECT outcome, COUNT(*) n FROM signals GROUP BY outcome").fetchall()
    counts = {r["outcome"]:r["n"] for r in rows}
    settled = counts.get("WIN",0)+counts.get("LOSS",0)+counts.get("DRAW",0)
    decisive = counts.get("WIN",0)+counts.get("LOSS",0)
    return {"total":sum(counts.values()),"wins":counts.get("WIN",0),"losses":counts.get("LOSS",0),
            "draws":counts.get("DRAW",0),"pending":counts.get("PENDING",0),
            "recorded_win_rate_percent":round(counts.get("WIN",0)/decisive*100,1) if decisive else None,
            "note":"This is only the rate of outcomes manually recorded by you; it is not a guarantee or a verified backtest."}
