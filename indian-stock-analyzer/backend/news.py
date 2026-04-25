from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

import feedparser


def _rss_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"


def fetch_news_for_topic(topic: str, limit: int = 5) -> list[dict[str, Any]]:
    feed = feedparser.parse(_rss_url(topic))
    out: list[dict[str, Any]] = []
    for entry in feed.entries[:limit]:
        out.append(
            {
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
                "link": entry.get("link", ""),
                "source": entry.get("source", {}).get("title", "Google News"),
            }
        )
    return out


def fetch_market_news() -> dict[str, list[dict[str, Any]]]:
    return {
        "NIFTY50": fetch_news_for_topic("Nifty 50 India stock market", limit=10),
        "BANKNIFTY": fetch_news_for_topic("BankNifty India", limit=10),
    }
