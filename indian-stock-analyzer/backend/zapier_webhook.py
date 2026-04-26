from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

IST = ZoneInfo("Asia/Kolkata")


def send_alert(stock: str, signal: str, price: float, confidence: float, reasons: list[str]) -> None:
    payload = {
        "stock": stock,
        "signal": signal,
        "price": price,
        "confidence": confidence,
        "reasons": reasons,
        "time": datetime.now(IST).strftime("%d %b %Y %H:%M IST"),
    }
    
    url = os.getenv("ZAPIER_WEBHOOK_URL")
    if url and "YOUR_ID" not in url:
        try:
            requests.post(url, json=payload, timeout=8)
        except requests.RequestException:
            pass
            
    _send_telegram(payload)


def _send_telegram(payload: dict) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    signal_emoji = "🟢" if "BUY" in payload['signal'] else ("🔴" if "SELL" in payload['signal'] else "⚪")
    reasons_str = "\n".join([f"• {r}" for r in payload['reasons']])
    
    msg = (
        f"{signal_emoji} *{payload['stock']} {payload['signal']}* {signal_emoji}\n\n"
        f"🎯 *Price:* ₹{payload['price']}\n"
        f"📊 *Confidence:* {payload['confidence']}%\n"
        f"⏰ *Time:* {payload['time']}\n\n"
        f"*Technical Reasons:*\n{reasons_str}\n\n"
        f"💡 _Automated Signal Generator_"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=8)
    except requests.RequestException as e:
        print(f"Telegram error: {e}")
