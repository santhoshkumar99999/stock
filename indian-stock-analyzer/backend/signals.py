from __future__ import annotations

from typing import Any


def _safe(value: Any, default: float = 0.0) -> float:
    return float(value) if value is not None else default


def generate_signal(indicators: dict[str, Any], sentiment: dict[str, Any]) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []

    rsi = indicators.get("rsi")
    macd = indicators.get("macd")
    macd_signal = indicators.get("macd_signal")
    ema20 = indicators.get("ema20")
    ema50 = indicators.get("ema50")
    ema200 = indicators.get("ema200")
    price = indicators.get("price")
    bb_lower = indicators.get("bb_lower")
    bb_upper = indicators.get("bb_upper")
    volume = indicators.get("volume")
    avg_volume = indicators.get("avg_volume")
    sentiment_score = _safe(sentiment.get("score"))

    if rsi is not None:
        if rsi < 30:
            score += 2
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 2
            reasons.append("RSI overbought")

    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            score += 1
            reasons.append("MACD bullish crossover")
        else:
            score -= 1

    if None not in (ema20, ema50, ema200):
        if ema20 > ema50 > ema200:
            score += 2
            reasons.append("Bullish EMA alignment")
        elif ema20 < ema50 < ema200:
            score -= 2

    if None not in (price, bb_lower, bb_upper):
        if price < bb_lower:
            score += 1
            reasons.append("Below lower Bollinger Band")
        elif price > bb_upper:
            score -= 1

    if volume is not None and avg_volume:
        if volume > avg_volume * 1.5:
            score += 1
            reasons.append("High volume")

    if sentiment_score > 0.2:
        score += 2
        reasons.append("Positive news sentiment")
    elif sentiment_score < -0.2:
        score -= 2
        reasons.append("Negative news sentiment")

    if score >= 4:
        return {"signal": "STRONG BUY", "confidence": min(score * 10, 95), "reasons": reasons}
    if score >= 2:
        return {"signal": "BUY", "confidence": min(score * 10, 75), "reasons": reasons}
    if score <= -4:
        return {"signal": "STRONG SELL", "confidence": min(abs(score) * 10, 95), "reasons": reasons}
    if score <= -2:
        return {"signal": "SELL", "confidence": min(abs(score) * 10, 75), "reasons": reasons}
    return {"signal": "HOLD", "confidence": 50, "reasons": reasons}
