import os, sqlite3, uuid
from datetime import datetime, timezone
from typing import Optional
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(APP_DIR, "signals.db"))
BASE_URL = "https://biquote.io"
SYMBOLS = {"EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD","USDCHF","NZDUSD","EURJPY","GBPJPY","XAUUSD"}
INTERVALS = {"1m","5m","15m","30m","1h"}

app = FastAPI(title="Mahim Quotex AI Signal Dashboard", version="4.0.0")
app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS signals(
            id TEXT PRIMARY KEY, created_at TEXT, symbol TEXT, interval TEXT,
            signal TEXT, strength INTEGER, entry REAL, rationale TEXT,
            outcome TEXT DEFAULT 'PENDING', evaluated_at TEXT
        )""")
init_db()

@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse(os.path.join(APP_DIR, "static", "index.html"))

def fetch_bars(symbol: str, interval: str, limit: int = 250):
    if symbol not in SYMBOLS:
        raise HTTPException(400, "Unsupported symbol")
    if interval not in INTERVALS:
        raise HTTPException(400, "Unsupported interval")
    try:
        r = requests.get(f"{BASE_URL}/api/{symbol}/ohlc",
                         params={"interval": interval, "limit": limit},
                         timeout=15)
        r.raise_for_status()
        payload = r.json()
        bars = payload.get("bars")
        if not isinstance(bars, list):
            raise ValueError("API response has no bars array")
        clean = []
        for b in bars:
            if b.get("isOpen") is True:
                continue
            row = {k: float(b[k]) for k in ("open","high","low","close")}
            row["openTime"] = b["openTime"]
            clean.append(row)
        clean.sort(key=lambda x: x["openTime"])
        if len(clean) < 60:
            raise ValueError(f"Only {len(clean)} closed candles available; need at least 60")
        return clean, payload
    except requests.RequestException as e:
        raise HTTPException(502, f"Market data provider error: {e}")
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(502, f"Invalid market data response: {e}")

def ema(values, period):
    alpha = 2/(period+1)
    out = [values[0]]
    for x in values[1:]:
        out.append(alpha*x + (1-alpha)*out[-1])
    return out

def rsi(values, period=14):
    gains, losses = [], []
    for a,b in zip(values[:-1], values[1:]):
        gains.append(max(b-a,0))
        losses.append(max(a-b,0))
    if len(gains) < period: return 50.0
    ag = sum(gains[:period])/period
    al = sum(losses[:period])/period
    for i in range(period, len(gains)):
        ag = (ag*(period-1)+gains[i])/period
        al = (al*(period-1)+losses[i])/period
    if al == 0: return 100.0
    return 100 - 100/(1+ag/al)

def analyse(bars):
    closes = [b["close"] for b in bars]
    e9, e21, e50 = ema(closes,9), ema(closes,21), ema(closes,50)
    r = rsi(closes)
    fast, slow = ema(closes,12), ema(closes,26)
    macd = [a-b for a,b in zip(fast,slow)]
    sigline = ema(macd,9)
    votes = []
    votes.append(1 if e9[-1] > e21[-1] else -1)
    votes.append(1 if e21[-1] > e50[-1] else -1)
    votes.append(1 if macd[-1] > sigline[-1] else -1)
    votes.append(1 if closes[-1] > closes[-2] else -1)
    if r >= 55: votes.append(1)
    elif r <= 45: votes.append(-1)
    else: votes.append(0)
    score = sum(votes)
    if score >= 3: signal = "CALL"
    elif score <= -3: signal = "PUT"
    else: signal = "WAIT"
    strength = min(95, 50 + abs(score)*9) if signal != "WAIT" else 50
    return {"signal":signal, "strength":strength, "rsi":round(r,2),
            "ema9":round(e9[-1],6), "ema21":round(e21[-1],6),
            "ema50":round(e50[-1],6), "macd":round(macd[-1],8),
            "votes":votes, "score":score}

@app.get("/api/health")
def health():
    return {"status":"ok","version":"4.0.0","database":"sqlite",
            "market_provider":"Biquote","quotex_feed":False,
            "otc_feed":False,"timestamp":datetime.now(timezone.utc).isoformat()}

@app.get("/api/market")
def market(symbol: str="EURUSD", interval: str="1m"):
    bars, payload = fetch_bars(symbol, interval)
    latest = bars[-1]
    return {"symbol":symbol,"interval":interval,"provider":"Biquote (MT5/Yahoo aggregated; not Quotex)",
            "latest_closed_candle":latest,"candles":bars[-120:]}

@app.get("/api/analyse")
def get_analysis(symbol: str="EURUSD", interval: str="1m", save: bool=True):
    bars, payload = fetch_bars(symbol, interval)
    result = analyse(bars)
    latest = bars[-1]
    # Avoid pretending this is a guaranteed expiry prediction.
    rationale = f"RSI {result['rsi']}; EMA9/21/50 and MACD confirmation; score {result['score']}."
    record_id = str(uuid.uuid4())
    if save:
        with db() as con:
            con.execute("""INSERT INTO signals(id,created_at,symbol,interval,signal,strength,entry,rationale)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (record_id,datetime.now(timezone.utc).isoformat(),symbol,interval,
                         result["signal"],result["strength"],latest["close"],rationale))
    return {"id":record_id if save else None,"symbol":symbol,"interval":interval,
            "signal":result["signal"],"strength_score":result["strength"],
            "strength_is_win_probability":False,"entry_reference":latest["close"],
            "candle_time":latest["openTime"],"indicators":result,
            "provider":"Biquote; not Quotex price feed",
            "warning":"Educational rule-based analysis only. Not financial advice; no win guarantee."}

@app.get("/api/history")
def history(limit: int=50):
    limit=max(1,min(limit,200))
    with db() as con:
        rows=con.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
    return [dict(x) for x in rows]

@app.post("/api/outcome/{signal_id}")
def outcome(signal_id: str, outcome: str):
    outcome=outcome.upper()
    if outcome not in {"WIN","LOSS","DRAW","PENDING"}:
        raise HTTPException(400,"Outcome must be WIN, LOSS, DRAW or PENDING")
    with db() as con:
        cur=con.execute("UPDATE signals SET outcome=?, evaluated_at=? WHERE id=?",
                        (outcome,datetime.now(timezone.utc).isoformat(),signal_id))
        if cur.rowcount == 0: raise HTTPException(404,"Signal not found")
    return {"ok":True,"id":signal_id,"outcome":outcome}

@app.get("/api/stats")
def stats():
    with db() as con:
        rows=con.execute("SELECT outcome, COUNT(*) n FROM signals GROUP BY outcome").fetchall()
    counts={r["outcome"]:r["n"] for r in rows}
    decided=counts.get("WIN",0)+counts.get("LOSS",0)+counts.get("DRAW",0)
    winrate=round(counts.get("WIN",0)/decided*100,2) if decided else None
    return {"total":sum(counts.values()),"wins":counts.get("WIN",0),
            "losses":counts.get("LOSS",0),"draws":counts.get("DRAW",0),
            "pending":counts.get("PENDING",0),"observed_win_rate_percent":winrate,
            "note":"Only manually evaluated outcomes; not a forecast or guarantee."}
