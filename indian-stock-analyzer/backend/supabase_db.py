"""
supabase_db.py — Supabase integration for Indian Stock Analyzer
================================================================
Provides a single shared Supabase client and helper functions to:
  • Persist trading signals (upsert on symbol+timestamp)
  • Log alert history
  • Read back latest signals / watchlist data

Tables expected in Supabase (run the SQL in supabase_schema.sql):
  - signals       (symbol, signal, confidence, price, reasons, risk_flags, data_status, created_at)
  - alerts        (symbol, signal, price, confidence, sent_at)
  - watchlist     (symbol, added_at)
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Client initialisation ─────────────────────────────────────────────────────

_supabase_client = None


def get_client():
    """Return (and lazily initialise) the shared Supabase client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        logger.warning("Supabase env vars not set — DB persistence disabled.")
        return None

    try:
        from supabase import create_client  # type: ignore

        _supabase_client = create_client(url, key)
        logger.info("✅ Supabase client initialised — URL: %s", url)
    except ImportError:
        logger.error("supabase-py not installed. Run: pip install supabase")
    except Exception as exc:
        logger.exception("Failed to initialise Supabase client: %s", exc)

    return _supabase_client


# ── Signals ───────────────────────────────────────────────────────────────────


def upsert_signal(symbol: str, payload: dict[str, Any]) -> bool:
    """
    Persist (or update) a trading signal row in the `signals` table.
    Returns True on success, False on failure.
    """
    client = get_client()
    if client is None:
        return False

    row = {
        "symbol":      symbol,
        "signal":      payload.get("signal", "HOLD"),
        "confidence":  payload.get("confidence", 0),
        "price":       payload.get("price"),
        "reasons":     payload.get("reasons", []),
        "risk_flags":  payload.get("risk_flags", []),
        "data_status": payload.get("data_status", "OK"),
        "created_at":  datetime.now(timezone.utc).isoformat(),
    }

    try:
        client.table("signals").upsert(row, on_conflict="symbol").execute()
        logger.debug("Upserted signal for %s → %s", symbol, row["signal"])
        return True
    except Exception as exc:
        logger.error("upsert_signal failed for %s: %s", symbol, exc)
        return False


def get_latest_signals(limit: int = 50) -> list[dict[str, Any]]:
    """Fetch the most-recently-updated signals from Supabase."""
    client = get_client()
    if client is None:
        return []

    try:
        response = (
            client.table("signals")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        logger.error("get_latest_signals failed: %s", exc)
        return []


def get_signal_for_symbol(symbol: str) -> dict[str, Any] | None:
    """Fetch the latest signal row for a specific symbol."""
    client = get_client()
    if client is None:
        return None

    try:
        response = (
            client.table("signals")
            .select("*")
            .eq("symbol", symbol.upper())
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None
    except Exception as exc:
        logger.error("get_signal_for_symbol failed for %s: %s", symbol, exc)
        return None


# ── Alerts ────────────────────────────────────────────────────────────────────


def log_alert(symbol: str, signal: str, price: float, confidence: int) -> bool:
    """
    Append an alert event to the `alerts` table for audit history.
    Returns True on success.
    """
    client = get_client()
    if client is None:
        return False

    row = {
        "symbol":     symbol,
        "signal":     signal,
        "price":      price,
        "confidence": confidence,
        "sent_at":    datetime.now(timezone.utc).isoformat(),
    }

    try:
        client.table("alerts").insert(row).execute()
        logger.info("Alert logged: %s %s @ %.2f", symbol, signal, price)
        return True
    except Exception as exc:
        logger.error("log_alert failed for %s: %s", symbol, exc)
        return False


def get_alert_history(limit: int = 100) -> list[dict[str, Any]]:
    """Return recent alert history rows."""
    client = get_client()
    if client is None:
        return []

    try:
        response = (
            client.table("alerts")
            .select("*")
            .order("sent_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        logger.error("get_alert_history failed: %s", exc)
        return []


# ── Watchlist ─────────────────────────────────────────────────────────────────


def get_watchlist() -> list[str]:
    """Return symbols currently in the watchlist table."""
    client = get_client()
    if client is None:
        return []

    try:
        response = client.table("watchlist").select("symbol").execute()
        return [row["symbol"] for row in (response.data or [])]
    except Exception as exc:
        logger.error("get_watchlist failed: %s", exc)
        return []


def add_to_watchlist(symbol: str) -> bool:
    """Add a symbol to the watchlist (ignore if already present)."""
    client = get_client()
    if client is None:
        return False

    try:
        client.table("watchlist").upsert(
            {"symbol": symbol.upper(), "added_at": datetime.now(timezone.utc).isoformat()},
            on_conflict="symbol",
        ).execute()
        return True
    except Exception as exc:
        logger.error("add_to_watchlist failed for %s: %s", symbol, exc)
        return False


def remove_from_watchlist(symbol: str) -> bool:
    """Remove a symbol from the watchlist."""
    client = get_client()
    if client is None:
        return False

    try:
        client.table("watchlist").delete().eq("symbol", symbol.upper()).execute()
        return True
    except Exception as exc:
        logger.error("remove_from_watchlist failed for %s: %s", symbol, exc)
        return False
