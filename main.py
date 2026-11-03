from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Literal
from statistics import mean
import os

app = FastAPI(
    title="Mahim Quotex AI Signal API",
    description="Educational technical-analysis API. Not financial advice.",
    version="1.1.0"
)

class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., examples=["EURUSD"])
    market: Literal["FOREX", "OTC"] = "FOREX"
    timeframe: Literal["1m", "5m", "15m"] = "1m"
    candles: List[Candle] = Field(..., min_length=55)

def ema(values, period):
    alpha = 2 / (period + 1)
    result = values[0]
    for value in values[1:]:
        result = alpha * value + (1 - alpha) * result
    return result

def rsi(values, period=14):
    changes = [values[i] - values[i-1] for i in range(1, len(values))]
    recent = changes[-period:]
    gains = [max(x, 0) for x in recent]
    losses = [max(-x, 0) for x in recent]
    avg_gain = mean(gains) if gains else 0
    avg_loss = mean(losses) if losses else 0
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

@app.get("/")
def dashboard():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(data: AnalyzeRequest):
    if data.market == "OTC":
        raise HTTPException(
            status_code=501,
            detail="OTC analysis is unavailable until a verified Quotex OTC candle feed is connected. Forex candles are not a substitute."
        )
    candles = data.candles
    if any(c.high < max(c.open, c.close) or c.low > min(c.open, c.close) or c.high < c.low for c in candles):
        raise HTTPException(status_code=422, detail="Invalid OHLC candle values.")
    closes = [c.close for c in candles]
    e9, e21, e50 = ema(closes, 9), ema(closes, 21), ema(closes, 50)
    r = round(rsi(closes), 2)

    # MACD direction from a short series of MACD values and its signal EMA.
    macd_series = []
    for i in range(25, len(closes) + 1):
        segment = closes[:i]
        macd_series.append(ema(segment, 12) - ema(segment, 26))
    macd_line = macd_series[-1]
    macd_signal = ema(macd_series, 9) if len(macd_series) >= 9 else macd_line
    macd_bull = macd_line > macd_signal
    macd_bear = macd_line < macd_signal

    bull_points = int(e9 > e21) + int(e21 > e50) + int(r > 50) + int(macd_bull)
    bear_points = int(e9 < e21) + int(e21 < e50) + int(r < 50) + int(macd_bear)

    if bull_points >= 3:
        signal, trend, score = "CALL", "BULLISH", 60 + bull_points * 8
    elif bear_points >= 3:
        signal, trend, score = "PUT", "BEARISH", 60 + bear_points * 8
    else:
        signal, trend, score = "WAIT", "MIXED", 0

    return {
        "symbol": data.symbol.upper(), "market": data.market,
        "timeframe": data.timeframe, "signal": signal,
        "confidence_score": min(score, 92),
        "confidence_is_win_probability": False,
        "indicators": {
            "rsi_14": r, "ema_9": round(e9, 6),
            "ema_21": round(e21, 6), "ema_50": round(e50, 6),
            "macd_direction": "BULLISH" if macd_bull else "BEARISH" if macd_bear else "NEUTRAL",
            "trend": trend
        },
        "latest_close": closes[-1],
        "disclaimer": "Educational technical analysis only. Not financial advice; no outcome is guaranteed."
    }

app.mount("/static", StaticFiles(directory="static"), name="static")
