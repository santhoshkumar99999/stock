from __future__ import annotations

import asyncio
from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo

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
    allow_origins=["http://localhost:3000"],
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
        sentiment = {"sentiment": "Neutral", "score": 0.0, "articles": []}
    signal = generate_signal(indicators, sentiment)
    return {
        "symbol": symbol,
        "price": indicators.get("price"),
        "indicators": indicators,
        "sentiment": sentiment,
        **signal,
    }


def refresh_all() -> None:
    for symbol in fetcher.get_nifty50_symbols():
        stock = build_stock_payload(symbol)
        prev = last_signals.get(symbol)
        now = stock["signal"]
        if prev != now and now in ("STRONG BUY", "STRONG SELL"):
            send_alert(symbol, now, stock.get("price") or 0.0, stock["confidence"], stock["reasons"])
        last_signals[symbol] = now


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


@app.get("/api/indices")
@limiter.limit("30/minute")
async def get_indices(request: Request) -> dict[str, Any]:
    indices = fetcher.get_index_live()
    return {
        "market_status": "OPEN" if is_market_open() else "CLOSED",
        "last_updated": datetime.now(IST).isoformat(),
        "indices": indices,
    }


@app.get("/api/stocks")
@limiter.limit("30/minute")
async def get_stocks(request: Request) -> list[dict[str, Any]]:
    return [build_stock_payload(s, include_news=False) for s in fetcher.get_nifty50_symbols()]


@app.get("/api/stock/{symbol}")
@limiter.limit("60/minute")
async def get_stock(request: Request, symbol: str) -> dict[str, Any]:
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
async def get_news(request: Request) -> dict[str, Any]:
    market_news = fetch_market_news()
    out = {
        "NIFTY50": score_articles(market_news["NIFTY50"]),
        "BANKNIFTY": score_articles(market_news["BANKNIFTY"]),
    }
    for symbol in fetcher.get_nifty50_symbols()[:15]:
        out[symbol] = score_articles(fetch_news_for_topic(f"{symbol} NSE India stock", limit=5))
    return out


@app.get("/api/signals/top")
@limiter.limit("30/minute")
async def top_signals(request: Request) -> dict[str, Any]:
    rows = [build_stock_payload(s, include_news=False) for s in fetcher.get_nifty50_symbols()]
    buys = sorted([r for r in rows if "BUY" in r["signal"]], key=lambda x: x["confidence"], reverse=True)[:5]
    sells = sorted([r for r in rows if "SELL" in r["signal"]], key=lambda x: x["confidence"], reverse=True)[:5]
    return {"top_buy": buys, "top_sell": sells}


@app.get("/api/banknifty")
@limiter.limit("30/minute")
async def banknifty_stocks(request: Request) -> list[dict[str, Any]]:
    return [build_stock_payload(s, include_news=False) for s in fetcher.get_banknifty_symbols()]


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
