from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, messaging

BASE_DIR = Path(__file__).resolve().parent
FCM_TOKENS_FILE = BASE_DIR / "fcm_tokens.json"
_firebase_ready = False


def _initialize_firebase() -> bool:
    global _firebase_ready
    if _firebase_ready:
        return True
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "./firebase-service-account.json")
    full_path = (BASE_DIR / cred_path).resolve() if not Path(cred_path).is_absolute() else Path(cred_path)
    if not full_path.exists():
        return False
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(full_path))
            firebase_admin.initialize_app(cred)
        _firebase_ready = True
        return True
    except Exception:
        return False


def save_fcm_token(token: str) -> bool:
    """Save FCM token sent by the PWA on load."""
    clean_token = (token or "").strip()
    if not clean_token:
        return False
    try:
        tokens = get_fcm_tokens()
        if clean_token not in tokens:
            tokens.append(clean_token)
            with FCM_TOKENS_FILE.open("w", encoding="utf-8") as f:
                json.dump(tokens, f)
        return True
    except Exception:
        return False


def get_fcm_tokens() -> list[str]:
    """Get all saved FCM tokens."""
    try:
        with FCM_TOKENS_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(item) for item in data if item]
    except Exception:
        pass
    return []


def send_push_notification(title: str, body: str, data: dict[str, Any] | None = None) -> bool:
    """
    Send push notification to all registered PWA instances.
    This pops up on your phone like a native app notification.
    """
    if not _initialize_firebase():
        return False

    tokens = get_fcm_tokens()
    if not tokens:
        return False

    sent = False
    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon="/icon-192.png",
                        badge="/badge-72.png",
                        vibrate=[200, 100, 200],
                    ),
                    fcm_options=messaging.WebpushFCMOptions(link="/"),
                ),
            )
            messaging.send(message)
            sent = True
        except Exception:
            continue
    return sent


def notify_strong_buy(symbol: str, price: float, confidence: int, reasons: list[str]) -> bool:
    return send_push_notification(
        title=f"STRONG BUY - {symbol}",
        body=f"INR {price} | Confidence: {confidence}%\n{reasons[0] if reasons else ''}",
        data={"type": "BUY", "symbol": symbol, "price": price},
    )


def notify_strong_sell(symbol: str, price: float, confidence: int, reasons: list[str]) -> bool:
    return send_push_notification(
        title=f"STRONG SELL - {symbol}",
        body=f"INR {price} | Confidence: {confidence}%\n{reasons[0] if reasons else ''}",
        data={"type": "SELL", "symbol": symbol, "price": price},
    )


def notify_market_open() -> bool:
    return send_push_notification(
        title="NSE Market OPEN",
        body="9:15 AM IST - Trading has started. Tap to see top signals.",
        data={"type": "MARKET_OPEN"},
    )


def notify_market_close() -> bool:
    return send_push_notification(
        title="NSE Market CLOSED",
        body="3:30 PM IST - Market closed. Tap to review today's signals.",
        data={"type": "MARKET_CLOSE"},
    )


def notify_custom(title: str, body: str) -> bool:
    return send_push_notification(title=title, body=body)
