from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from callmebot import (
    send_market_close_alert,
    send_market_open_alert,
    send_strong_buy_alert,
    send_strong_sell_alert,
)
from fcm_notifications import (
    notify_market_close,
    notify_market_open,
    notify_strong_buy,
    notify_strong_sell,
)
from fetcher import DataFetcher
from indicators import calculate_indicators
from signals import generate_signal

IST = ZoneInfo("Asia/Kolkata")
scheduler = BackgroundScheduler(timezone=IST)
ALERTED_TODAY: set[str] = set()
fetcher = DataFetcher(ttl_minutes=5)
ALERT_STATUS_FILE = Path(__file__).resolve().parent / "alert_status.txt"
_started = False


def _hist_to_ohlcv(hist):
    rows = []
    for idx, row in hist.iterrows():
        rows.append(
            {
                "time": idx.to_pydatetime().astimezone(IST).isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            }
        )
    return rows


def is_alerts_enabled() -> bool:
    try:
        return ALERT_STATUS_FILE.read_text(encoding="utf-8").strip().upper() == "ON"
    except Exception:
        return False


def scan_and_alert() -> None:
    if not is_alerts_enabled():
        return
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return
    if not ((now.hour > 9 or (now.hour == 9 and now.minute >= 15)) and (now.hour < 15 or (now.hour == 15 and now.minute <= 30))):
        return
    for sym in fetcher.get_nifty50_symbols():
        alert_key = f"{sym}_{now.date().isoformat()}"
        if alert_key in ALERTED_TODAY:
            continue
        try:
            hist = yf.Ticker(f"{sym}.NS").history(period="1mo")
            if hist.empty:
                continue
            ind = calculate_indicators(_hist_to_ohlcv(hist))
            sig = generate_signal(ind, {"score": 0, "sentiment": "Neutral"})
            if sig["signal"] == "STRONG BUY":
                price = round(float(hist["Close"].iloc[-1]), 2)
                notify_strong_buy(sym, price, int(sig["confidence"]), sig["reasons"])
                send_strong_buy_alert(sym, price, int(sig["confidence"]), sig["reasons"])
                ALERTED_TODAY.add(alert_key)
            elif sig["signal"] == "STRONG SELL":
                price = round(float(hist["Close"].iloc[-1]), 2)
                notify_strong_sell(sym, price, int(sig["confidence"]), sig["reasons"])
                send_strong_sell_alert(sym, price, int(sig["confidence"]), sig["reasons"])
                ALERTED_TODAY.add(alert_key)
        except Exception:
            continue


def reset_daily_alerts() -> None:
    ALERTED_TODAY.clear()


def _send_market_open_if_enabled() -> None:
    if is_alerts_enabled():
        notify_market_open()
        send_market_open_alert()


def _send_market_close_if_enabled() -> None:
    if is_alerts_enabled():
        notify_market_close()
        send_market_close_alert()


def setup_scheduler() -> None:
    global _started
    if _started:
        return
    scheduler.add_job(scan_and_alert, "interval", minutes=10, id="bot_stock_scan")
    scheduler.add_job(
        _send_market_open_if_enabled,
        CronTrigger(day_of_week="mon-fri", hour=9, minute=15, timezone=IST),
        id="bot_market_open",
    )
    scheduler.add_job(
        _send_market_close_if_enabled,
        CronTrigger(day_of_week="mon-fri", hour=15, minute=30, timezone=IST),
        id="bot_market_close",
    )
    scheduler.add_job(
        reset_daily_alerts,
        CronTrigger(hour=0, minute=0, timezone=IST),
        id="bot_reset_alerts",
    )
    scheduler.start()
    _started = True
