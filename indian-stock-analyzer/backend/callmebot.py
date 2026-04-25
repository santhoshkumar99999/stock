from __future__ import annotations

import os
from urllib.parse import quote

import requests

PHONE = os.getenv("CALLMEBOT_PHONE")
API_KEY = os.getenv("CALLMEBOT_APIKEY")


def send_callmebot_alert(message: str) -> bool:
    """Send WhatsApp message via CallMeBot free API."""
    if not PHONE or not API_KEY:
        return False
    encoded_msg = quote(message)
    url = (
        "https://api.callmebot.com/whatsapp.php"
        f"?phone={PHONE}&text={encoded_msg}&apikey={API_KEY}"
    )
    try:
        resp = requests.get(url, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def send_strong_buy_alert(symbol: str, price: float, confidence: int, reasons: list[str]) -> bool:
    message = (
        "🟢 *STRONG BUY ALERT*\n\n"
        f"Stock: *{symbol}*\n"
        f"Price: ₹{price}\n"
        f"Confidence: {confidence}%\n\n"
        "Reasons:\n"
        + "\n".join([f"• {r}" for r in reasons[:3]])
        + f"\n\nReply `SIGNAL {symbol}` for full analysis"
    )
    return send_callmebot_alert(message)


def send_strong_sell_alert(symbol: str, price: float, confidence: int, reasons: list[str]) -> bool:
    message = (
        "🔴 *STRONG SELL ALERT*\n\n"
        f"Stock: *{symbol}*\n"
        f"Price: ₹{price}\n"
        f"Confidence: {confidence}%\n\n"
        "Reasons:\n"
        + "\n".join([f"• {r}" for r in reasons[:3]])
        + f"\n\nReply `SIGNAL {symbol}` for full analysis"
    )
    return send_callmebot_alert(message)


def send_market_open_alert() -> bool:
    return send_callmebot_alert(
        "📊 *NSE Market OPEN* — 9:15 AM IST\n\nSend `TOP5` for today's best buy signals."
    )


def send_market_close_alert() -> bool:
    return send_callmebot_alert(
        "📊 *NSE Market CLOSED* — 3:30 PM IST\n\nSend `TOP5` to review today's signals."
    )
