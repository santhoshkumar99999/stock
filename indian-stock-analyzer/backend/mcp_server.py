from __future__ import annotations

import asyncio
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from fetcher import DataFetcher
from indicators import calculate_indicators
from news import fetch_news_for_topic, fetch_market_news
from sentiment import score_articles
from signals import generate_signal
from dotenv import load_dotenv
import requests

load_dotenv()
mcp = FastMCP("indian-stock-analyzer")
fetcher = DataFetcher()


def _stock_signal(symbol: str) -> dict[str, Any]:
    ohlcv = fetcher.get_ohlcv(symbol, "1d")
    ind = calculate_indicators(ohlcv)
    sentiment = score_articles(fetch_news_for_topic(f"{symbol} NSE India stock", 5))
    signal = generate_signal(ind, sentiment)
    return {"symbol": symbol, "indicators": ind, "sentiment": sentiment, **signal}


@mcp.tool()
async def get_top_buy_signals() -> list[dict[str, Any]]:
    rows = [_stock_signal(s) for s in fetcher.get_nifty50_symbols()]
    buys = [r for r in rows if "BUY" in r["signal"]]
    buys.sort(key=lambda x: x["confidence"], reverse=True)
    return buys[:5]


@mcp.tool()
async def get_stock_signal(symbol: str) -> dict[str, Any]:
    return _stock_signal(symbol.upper())


@mcp.tool()
async def get_market_sentiment() -> dict[str, Any]:
    market_news = fetch_market_news()
    return {
        "NIFTY50": score_articles(market_news["NIFTY50"]),
        "BANKNIFTY": score_articles(market_news["BANKNIFTY"]),
    }


@mcp.tool()
async def send_zapier_alert(stock: str, signal: str, price: float) -> dict[str, Any]:
    url = os.getenv("ZAPIER_WEBHOOK_URL")
    if not url:
        return {"ok": False, "error": "ZAPIER_WEBHOOK_URL missing"}
    r = requests.post(url, json={"stock": stock, "signal": signal, "price": price}, timeout=10)
    return {"ok": r.ok, "status_code": r.status_code}


@mcp.tool()
async def get_news_sentiment(stock: str) -> dict[str, Any]:
    articles = fetch_news_for_topic(f"{stock} NSE India stock", 5)
    return score_articles(articles)


if __name__ == "__main__":
    asyncio.run(mcp.run_stdio_async())
