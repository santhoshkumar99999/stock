from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo
import time

import requests
import yfinance as yf

IST = ZoneInfo("Asia/Kolkata")

NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN",
    "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "BAJFINANCE",
    "TITAN", "SUNPHARMA", "ULTRACEMCO", "WIPRO", "HCLTECH", "ONGC", "NTPC", "POWERGRID",
    "BAJAJFINSV", "TECHM", "NESTLEIND", "TATAMOTORS", "ADANIENT", "JSWSTEEL", "COALINDIA",
    "TATASTEEL", "DIVISLAB", "CIPLA", "BRITANNIA", "DRREDDY", "APOLLOHOSP", "EICHERMOT",
    "GRASIM", "HEROMOTOCO", "HINDALCO", "INDUSINDBK", "M&M", "SBILIFE", "BPCL", "ADANIPORTS",
    "TATACONSUM", "UPL", "BAJAJ-AUTO", "HDFCLIFE", "VEDL",
]

BANKNIFTY_SYMBOLS = [
    "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK",
    "BANKBARODA", "PNB", "FEDERALBNK", "IDFCFIRSTB", "BANDHANBNK", "AUBANK",
]

INDEX_MAP = {"NIFTY50": "^NSEI", "BANKNIFTY": "^NSEBANK"}
TIMEFRAME_MAP = {"1d": "1mo", "1wk": "6mo", "1mo": "2y"}
INTERVAL_MAP = {"1d": "1d", "1wk": "1wk", "1mo": "1mo"}


@dataclass
class CacheItem:
    data: Any
    timestamp: datetime


class DataFetcher:
    def __init__(self, ttl_minutes: int = 5) -> None:
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache: dict[str, CacheItem] = {}
        self.nse_session = requests.Session()
        self._init_nse_session()

    def _init_nse_session(self) -> None:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://www.nseindia.com",
        }
        self.nse_session.headers.update(headers)
        try:
            self.nse_session.get("https://www.nseindia.com", timeout=10)
            time.sleep(1)
        except requests.RequestException:
            pass

    def _is_stale(self, key: str) -> bool:
        item = self.cache.get(key)
        if not item:
            return True
        return datetime.now(IST) - item.timestamp > self.ttl

    def _set_cache(self, key: str, data: Any) -> Any:
        self.cache[key] = CacheItem(data=data, timestamp=datetime.now(IST))
        return data

    def get_index_live(self) -> dict[str, Any]:
        key = "indices_live"
        if not self._is_stale(key):
            return self.cache[key].data
        payload: dict[str, Any] = {}
        for name, ticker in INDEX_MAP.items():
            tk = yf.Ticker(ticker)
            hist = tk.history(period="5d", interval="1d")
            if hist.empty:
                payload[name] = {"price": None, "change_percent": None}
                continue
            last = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
            chg = ((last - prev) / prev) * 100 if prev else 0.0
            payload[name] = {"price": last, "change_percent": chg}
        return self._set_cache(key, payload)

    def get_ohlcv(self, symbol: str, timeframe: str = "1d") -> list[dict[str, Any]]:
        tf = timeframe if timeframe in TIMEFRAME_MAP else "1d"
        key = f"ohlcv:{symbol}:{tf}"
        if not self._is_stale(key):
            return self.cache[key].data
        ticker = symbol if symbol.startswith("^") else f"{symbol}.NS"
        tk = yf.Ticker(ticker)
        hist = tk.history(period=TIMEFRAME_MAP[tf], interval=INTERVAL_MAP[tf])
        out: list[dict[str, Any]] = []
        for idx, row in hist.iterrows():
            out.append(
                {
                    "time": idx.to_pydatetime().astimezone(IST).isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                }
            )
        return self._set_cache(key, out)

    def get_nifty50_symbols(self) -> list[str]:
        return NIFTY_50_SYMBOLS

    def get_banknifty_symbols(self) -> list[str]:
        return BANKNIFTY_SYMBOLS

    def get_nse_nifty_snapshot(self) -> list[dict[str, Any]]:
        key = "nse_nifty_snapshot"
        if not self._is_stale(key):
            return self.cache[key].data
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        try:
            response = self.nse_session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json().get("data", [])
            time.sleep(1)
            return self._set_cache(key, data)
        except requests.RequestException:
            return self.cache[key].data if key in self.cache else []
