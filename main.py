from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Literal
from datetime import datetime,timezone
import os,requests
app=FastAPI(title="Mahim Quotex AI",version="3.0")
KEY=os.getenv("TWELVE_DATA_API_KEY","").strip()
@app.get("/")
def home(): return FileResponse("static/index.html")
@app.get("/health")
def health(): return {"status":"ok","version":"3.0"}
@app.get("/api/candles")
def candles(symbol:str="EUR/USD",interval:str="1min",market:Literal["FOREX","OTC"]="FOREX"):
 if market=="OTC": raise HTTPException(501,"Quotex OTC verified live feed unavailable. OTC remains WAIT.")
 if not KEY: raise HTTPException(503,"Render Environment-এ TWELVE_DATA_API_KEY সেট করুন।")
 if interval not in ["1min","5min","15min"]: raise HTTPException(400,"Invalid timeframe")
 try:
  r=requests.get("https://api.twelvedata.com/time_series",params={"symbol":symbol,"interval":interval,"outputsize":100,"apikey":KEY},timeout=20)
  d=r.json()
  if "values" not in d: raise HTTPException(502,d.get("message","Provider data unavailable"))
  rows=list(reversed(d["values"]))
  cs=[{"time":int(datetime.fromisoformat(x["datetime"]).replace(tzinfo=timezone.utc).timestamp()),"open":float(x["open"]),"high":float(x["high"]),"low":float(x["low"]),"close":float(x["close"])} for x in rows]
  return {"candles":cs,"source":"Twelve Data","updated_at":datetime.now(timezone.utc).isoformat()}
 except HTTPException: raise
 except Exception as e: raise HTTPException(502,str(e))
class Payload(BaseModel):
 candles:list[dict]
 symbol:str
 timeframe:str
def ema(v,n):
 k=2/(n+1);x=v[0]
 for a in v[1:]: x=a*k+x*(1-k)
 return x
@app.post("/api/analyze")
def analyze(p:Payload):
 if len(p.candles)<55: raise HTTPException(400,"At least 55 candles required")
 c=[float(x["close"]) for x in p.candles]; ch=[c[i]-c[i-1] for i in range(1,len(c))]
 g=sum(max(x,0) for x in ch[-14:])/14;l=sum(max(-x,0) for x in ch[-14:])/14
 rsi=100 if l==0 and g else (50 if l==0 else 100-100/(1+g/l))
 e9,e21,e50=ema(c,9),ema(c,21),ema(c,50);m=ema(c,12)-ema(c,26)
 bull=sum([e9>e21,e21>e50,rsi>52,m>0,c[-1]>c[-2]])
 bear=sum([e9<e21,e21<e50,rsi<48,m<0,c[-1]<c[-2]])
 sig="CALL" if bull>=4 else "PUT" if bear>=4 else "WAIT"
 return {"signal":sig,"score":max(bull,bear)*20,"last_price":c[-1],"indicators":{"rsi":round(rsi,2),"ema9":e9,"ema21":e21,"ema50":e50,"trend":"BULLISH" if bull>=4 else "BEARISH" if bear>=4 else "MIXED"},"reasons":[f"EMA9/21: {'up' if e9>e21 else 'down'}",f"RSI: {rsi:.1f}",f"Bull checks {bull}/5",f"Bear checks {bear}/5"]}
app.mount("/static",StaticFiles(directory="static"),name="static")
