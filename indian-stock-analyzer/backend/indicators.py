from __future__ import annotations

from typing import Any

import pandas as pd
import pandas_ta as ta


def _latest_from_prefix(df: pd.DataFrame | None, prefix: str) -> float | None:
    if df is None:
        return None
    cols = [c for c in df.columns if c.startswith(prefix)]
    if not cols:
        return None
    value = df[cols[0]].iloc[-1]
    return float(value) if pd.notna(value) else None


def calculate_indicators(ohlcv: list[dict[str, Any]]) -> dict[str, Any]:
    if not ohlcv:
        return {}
    df = pd.DataFrame(ohlcv)
    df["close"] = pd.to_numeric(df["close"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    df["volume"] = pd.to_numeric(df["volume"])

    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
    bbands = ta.bbands(df["close"], length=20, std=2)
    df["ema20"] = ta.ema(df["close"], length=20)
    df["ema50"] = ta.ema(df["close"], length=50)
    df["ema200"] = ta.ema(df["close"], length=200)
    df["atr14"] = ta.atr(df["high"], df["low"], df["close"], length=14)
    df["support"] = df["low"].rolling(20).min()
    df["resistance"] = df["high"].rolling(20).max()
    df["avg_volume"] = df["volume"].rolling(20).mean()

    row = df.iloc[-1]
    return {
        "price": float(row["close"]),
        "rsi": float(row["rsi"]) if pd.notna(row["rsi"]) else None,
        "macd": _latest_from_prefix(macd, "MACD_"),
        "macd_signal": _latest_from_prefix(macd, "MACDs_"),
        "bb_lower": _latest_from_prefix(bbands, "BBL_"),
        "bb_upper": _latest_from_prefix(bbands, "BBU_"),
        "ema20": float(row["ema20"]) if pd.notna(row["ema20"]) else None,
        "ema50": float(row["ema50"]) if pd.notna(row["ema50"]) else None,
        "ema200": float(row["ema200"]) if pd.notna(row["ema200"]) else None,
        "support": float(row["support"]) if pd.notna(row["support"]) else None,
        "resistance": float(row["resistance"]) if pd.notna(row["resistance"]) else None,
        "volume": float(row["volume"]),
        "avg_volume": float(row["avg_volume"]) if pd.notna(row["avg_volume"]) else None,
        "atr14": float(row["atr14"]) if pd.notna(row["atr14"]) else None,
    }
