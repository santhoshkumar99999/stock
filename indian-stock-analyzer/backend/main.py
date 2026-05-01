from __future__ import annotations

import asyncio
from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from bot_commands import handle_command
from bot_scheduler import setup_scheduler
from fcm_notifications import notify_custom, save_fcm_token
from fetcher import DataFetcher
from indicators import calculate_indicators
from news import fetch_market_news, fetch_news_for_topic
from scheduler import start_scheduler
from sentiment import score_articles
from signals import generate_signal
from zapier_webhook import send_alert
import supabase_db

load_dotenv()
IST = ZoneInfo("Asia/Kolkata")
fetcher = DataFetcher(ttl_minutes=5)
last_signals: dict[str, str] = {}

app = FastAPI(title="Indian Stock Analyzer")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_market_open() -> bool:
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    return time(9, 15) <= now.time() <= time(15, 30)


def build_stock_payload(symbol: str, include_news: bool = False) -> dict[str, Any]:
    ohlcv = fetcher.get_ohlcv(symbol, "1d")
    indicators = calculate_indicators(ohlcv)
    if include_news:
        articles = fetch_news_for_topic(f"{symbol} NSE India stock", limit=5)
        sentiment = score_articles(articles)
    else:
        sentiment = {"sentiment": "Neutral", "score": 0.0, "article_count": 0, "articles": []}
    signal = generate_signal(indicators, sentiment)
    return {
        "symbol":           symbol,
        "price":            indicators.get("price"),
        "indicators":       indicators,
        "sentiment":        sentiment,
        # Core signal fields
        "signal":           signal.get("signal", "HOLD"),
        "confidence":       signal.get("confidence", 0),
        "reasons":          signal.get("reasons", []),
        # Extended structured fields
        "confidence_label": signal.get("confidence_label", "LOW"),
        "confidence_score": signal.get("confidence_score", 0.0),
        "sentiment_tier":   signal.get("sentiment_tier", "SENTIMENT_NEUTRAL"),
        "key_drivers":      signal.get("key_drivers", []),
        "risk_flags":       signal.get("risk_flags", []),
        "data_status":      signal.get("data_status", "OK"),
        "disclaimer":       signal.get("disclaimer", ""),
        "signal_timestamp": signal.get("signal_timestamp", ""),
    }


def refresh_all() -> None:
    symbols = list(set(fetcher.get_nifty50_symbols() + fetcher.get_banknifty_symbols()))
    
    def process_symbol(symbol: str):
        stock = build_stock_payload(symbol)
        now_signal = stock["signal"]
        return symbol, stock, now_signal
        
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_symbol, symbols)
        for symbol, stock, now_signal in results:
            prev = last_signals.get(symbol)
            # Persist latest signal to Supabase
            supabase_db.upsert_signal(symbol, stock)
            # Trigger on state change to any BUY or SELL (including STRONG variants)
            if prev != now_signal and any(s in now_signal for s in ["BUY", "SELL"]) and "HOLD" not in now_signal:
                send_alert(symbol, now_signal, stock.get("price") or 0.0, stock["confidence"], stock["reasons"])
                supabase_db.log_alert(symbol, now_signal, stock.get("price") or 0.0, stock["confidence"])
            last_signals[symbol] = now_signal


class FCMTokenRequest(BaseModel):
    token: str


class CommandRequest(BaseModel):
    command: str


@app.on_event("startup")
async def startup_event() -> None:
    start_scheduler(refresh_all)
    setup_scheduler()
    asyncio.create_task(asyncio.to_thread(refresh_all))


@app.post("/api/fcm/register")
async def register_fcm_token(req: FCMTokenRequest) -> dict[str, str]:
    """PWA calls this on load to register for push notifications."""
    saved = save_fcm_token(req.token)
    return {"status": "registered" if saved else "ignored"}


@app.post("/api/fcm/test")
async def test_fcm_notification() -> dict[str, str]:
    """Test endpoint to verify FCM delivery."""
    sent = notify_custom("Test Notification", "FCM is working! Stock alerts will appear like this.")
    return {"status": "sent" if sent else "not_sent"}


@app.post("/api/command")
@limiter.limit("60/minute")
async def run_bot_command(request: Request, req: CommandRequest) -> dict[str, str]:
    """Run bot command from PWA command input."""
    response = handle_command((req.command or "").strip().upper())
    return {"response": response}


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Simple liveness probe — frontend can ping this to verify backend is up."""
    return {"status": "ok", "server": "Indian Stock Analyzer"}


@app.get("/api/indices")
@limiter.limit("30/minute")
def get_indices(request: Request) -> dict[str, Any]:
    indices = fetcher.get_index_live()
    return {
        "market_status": "OPEN" if is_market_open() else "CLOSED",
        "last_updated": datetime.now(IST).isoformat(),
        "indices": indices,
    }


@app.get("/api/stocks")
@limiter.limit("30/minute")
def get_stocks(request: Request) -> list[dict[str, Any]]:
    symbols = fetcher.get_nifty50_symbols()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda s: build_stock_payload(s, include_news=False), symbols))
    return results


@app.get("/api/stock/{symbol}")
@limiter.limit("60/minute")
def get_stock(request: Request, symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    if symbol not in fetcher.get_nifty50_symbols() and symbol not in fetcher.get_banknifty_symbols():
        return {"error": "Symbol not tracked"}
    return {
        "stock": build_stock_payload(symbol, include_news=True),
        "ohlcv": fetcher.get_ohlcv(symbol, "1d"),
        "ohlcv_1w": fetcher.get_ohlcv(symbol, "1wk"),
        "ohlcv_1m": fetcher.get_ohlcv(symbol, "1mo"),
    }


@app.get("/api/news")
@limiter.limit("30/minute")
def get_news(request: Request) -> dict[str, Any]:
    market_news = fetch_market_news()
    out = {
        "NIFTY50": score_articles(market_news["NIFTY50"]),
        "BANKNIFTY": score_articles(market_news["BANKNIFTY"]),
    }
    
    symbols = fetcher.get_nifty50_symbols()[:15]
    def fetch_news(sym: str):
        return sym, score_articles(fetch_news_for_topic(f"{sym} NSE India stock", limit=5))
        
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_news, symbols)
        for sym, articles in results:
            out[sym] = articles
            
    return out


@app.get("/api/signals/top")
@limiter.limit("30/minute")
def top_signals(request: Request) -> dict[str, Any]:
    symbols = fetcher.get_nifty50_symbols()
    with ThreadPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(lambda s: build_stock_payload(s, include_news=False), symbols))
    buys = sorted([r for r in rows if "BUY" in r["signal"]], key=lambda x: x["confidence"], reverse=True)[:5]
    sells = sorted([r for r in rows if "SELL" in r["signal"]], key=lambda x: x["confidence"], reverse=True)[:5]
    return {"top_buy": buys, "top_sell": sells}


@app.get("/api/banknifty")
@limiter.limit("30/minute")
def banknifty_stocks(request: Request) -> list[dict[str, Any]]:
    symbols = fetcher.get_banknifty_symbols()
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda s: build_stock_payload(s, include_news=False), symbols))
    return results


@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        await websocket.send_json(
            {
                "timestamp": datetime.now(IST).isoformat(),
                "market_status": "OPEN" if is_market_open() else "CLOSED",
                "indices": fetcher.get_index_live(),
            }
        )
        await asyncio.sleep(30)


# ── Supabase-backed DB endpoints ─────────────────────────────────────────────

@app.get("/api/db/signals")
@limiter.limit("30/minute")
def db_get_signals(request: Request, limit: int = 50) -> list[dict[str, Any]]:
    """Return persisted signals from Supabase (most recent first)."""
    return supabase_db.get_latest_signals(limit=limit)


@app.get("/api/db/signals/{symbol}")
@limiter.limit("60/minute")
def db_get_signal_symbol(request: Request, symbol: str) -> dict[str, Any]:
    """Return latest persisted signal for a specific symbol."""
    row = supabase_db.get_signal_for_symbol(symbol.upper())
    return row if row else {"error": "No signal found for symbol"}


@app.get("/api/db/alerts")
@limiter.limit("30/minute")
def db_get_alerts(request: Request, limit: int = 100) -> list[dict[str, Any]]:
    """Return alert history log from Supabase."""
    return supabase_db.get_alert_history(limit=limit)


@app.get("/api/db/watchlist")
@limiter.limit("30/minute")
def db_get_watchlist(request: Request) -> list[str]:
    """Return the watchlist symbols from Supabase."""
    return supabase_db.get_watchlist()


class WatchlistRequest(BaseModel):
    symbol: str


@app.post("/api/db/watchlist")
@limiter.limit("30/minute")
def db_add_watchlist(request: Request, req: WatchlistRequest) -> dict[str, Any]:
    """Add a symbol to the Supabase watchlist."""
    ok = supabase_db.add_to_watchlist(req.symbol)
    return {"status": "added" if ok else "error", "symbol": req.symbol.upper()}


@app.delete("/api/db/watchlist/{symbol}")
@limiter.limit("30/minute")
def db_remove_watchlist(request: Request, symbol: str) -> dict[str, Any]:
    """Remove a symbol from the Supabase watchlist."""
    ok = supabase_db.remove_from_watchlist(symbol)
    return {"status": "removed" if ok else "error", "symbol": symbol.upper()}

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        import traceback
        with open("startup_error.log", "w") as f:
            f.write(traceback.format_exc())
        raise

