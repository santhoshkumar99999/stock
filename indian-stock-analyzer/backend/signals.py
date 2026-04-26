from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

DISCLAIMER = (
    "This signal is for informational purposes only. "
    "Not financial advice. Always consult a licensed advisor before trading."
)


def _safe(value: Any, default: float = 0.0) -> float:
    """Safely cast to float, returning default on None/NaN."""
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sentiment_matrix(score: float, label: str) -> tuple[str, str]:
    """
    Apply the sentiment decision matrix.
    Returns (raw_signal, confidence_tier).

    Score range  | Label           | Signal
    +0.6 → +1.0  | positive        | BUY
    +0.2 → +0.59 | positive        | HOLD  (weak buy)
    -0.2 → +0.19 | neutral / mixed | HOLD
    -0.6 → -0.21 | negative        | HOLD  (weak sell)
    -1.0 → -0.61 | negative        | SELL
    null/missing  | any             | HOLD
    """
    label_lower = label.lower()

    if score >= 0.6 and label_lower == "bullish":
        return "BUY", "SENTIMENT_STRONG_BUY"
    if 0.2 <= score < 0.6 and label_lower == "bullish":
        return "HOLD", "SENTIMENT_WEAK_BUY"
    if -0.2 <= score <= 0.19:
        return "HOLD", "SENTIMENT_NEUTRAL"
    if -0.6 <= score < -0.2 and label_lower == "bearish":
        return "HOLD", "SENTIMENT_WEAK_SELL"
    if score <= -0.61 and label_lower == "bearish":
        return "SELL", "SENTIMENT_STRONG_SELL"

    return "HOLD", "SENTIMENT_NEUTRAL"


def generate_signal(indicators: dict[str, Any], sentiment: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a structured trading signal combining technical indicators
    and news/sentiment analysis. Always returns a valid dict — never raises.
    """
    try:
        return _compute_signal(indicators, sentiment)
    except Exception as exc:  # noqa: BLE001
        return _fallback_signal(risk_flags=[f"INTERNAL_ERROR: {exc}"])


def _compute_signal(indicators: dict[str, Any], sentiment: dict[str, Any]) -> dict[str, Any]:
    # ── Data-status tracking ────────────────────────────────────────────────
    data_status = "OK"
    if not indicators:
        data_status = "FALLBACK"
        return _fallback_signal(risk_flags=["NO_INDICATOR_DATA"])

    if not sentiment or sentiment.get("score") is None:
        data_status = "PARTIAL"

    # ── Extract values ───────────────────────────────────────────────────────
    rsi         = indicators.get("rsi")
    macd        = indicators.get("macd")
    macd_signal = indicators.get("macd_signal")
    ema20       = indicators.get("ema20")
    ema50       = indicators.get("ema50")
    ema200      = indicators.get("ema200")
    price       = indicators.get("price")
    bb_lower    = indicators.get("bb_lower")
    bb_upper    = indicators.get("bb_upper")
    volume      = indicators.get("volume")
    avg_volume  = indicators.get("avg_volume")
    atr14       = indicators.get("atr14")

    sentiment_score = _safe(sentiment.get("score"))
    sentiment_label = sentiment.get("sentiment", "Neutral")
    articles        = sentiment.get("articles", [])
    article_count   = len(articles)

    # ── Technical scoring ────────────────────────────────────────────────────
    tech_score = 0
    reasons: list[str] = []
    risk_flags: list[str] = []

    # RSI
    if rsi is not None:
        if rsi < 30:
            tech_score += 2
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            tech_score -= 2
            reasons.append(f"RSI overbought ({rsi:.1f})")
            risk_flags.append("RSI_OVERBOUGHT")
    else:
        risk_flags.append("RSI_MISSING")

    # MACD
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            tech_score += 1
            reasons.append("MACD bullish crossover")
        else:
            tech_score -= 1
            reasons.append("MACD bearish crossover")
    else:
        risk_flags.append("MACD_MISSING")

    # EMA alignment
    if None not in (ema20, ema50, ema200):
        if ema20 > ema50 > ema200:
            tech_score += 2
            reasons.append("Bullish EMA alignment (20 > 50 > 200)")
        elif ema20 < ema50 < ema200:
            tech_score -= 2
            reasons.append("Bearish EMA alignment (20 < 50 < 200)")
    else:
        risk_flags.append("EMA_PARTIAL")

    # Bollinger Bands
    if None not in (price, bb_lower, bb_upper):
        if price < bb_lower:
            tech_score += 1
            reasons.append("Price below lower Bollinger Band (potential reversal)")
        elif price > bb_upper:
            tech_score -= 1
            reasons.append("Price above upper Bollinger Band (potential reversal)")
            risk_flags.append("PRICE_ABOVE_BB_UPPER")

    # Volume spike
    if volume is not None and avg_volume:
        if volume > avg_volume * 1.5:
            tech_score += 1
            reasons.append(f"Volume spike ({volume / avg_volume:.1f}x average)")

    # ATR-based volatility warning
    if atr14 is not None and price:
        atr_pct = (atr14 / price) * 100
        if atr_pct > 3.0:
            risk_flags.append(f"HIGH_VOLATILITY (ATR {atr_pct:.1f}% of price)")

    # ── Sentiment layer ──────────────────────────────────────────────────────
    sent_signal, sent_tier = _sentiment_matrix(sentiment_score, sentiment_label)

    if sentiment_score > 0.2:
        tech_score += 2
        reasons.append(f"Positive news sentiment (score: {sentiment_score:.2f})")
    elif sentiment_score < -0.2:
        tech_score -= 2
        reasons.append(f"Negative news sentiment (score: {sentiment_score:.2f})")

    # Contradictory sentiment → flag risk
    if 0.4 <= abs(sentiment_score) <= 0.6:
        risk_flags.append("SENTIMENT_BORDERLINE")

    if article_count == 0:
        risk_flags.append("NO_NEWS_ARTICLES")
        data_status = "PARTIAL" if data_status == "OK" else data_status

    # ── Determine final signal ───────────────────────────────────────────────
    if tech_score >= 5:
        raw_signal = "STRONG BUY"
    elif tech_score >= 2:
        raw_signal = "BUY"
    elif tech_score <= -5:
        raw_signal = "STRONG SELL"
    elif tech_score <= -2:
        raw_signal = "SELL"
    else:
        raw_signal = "HOLD"

    # Sentiment override: if sentiment says SELL but technicals say BUY, flag it
    if sent_signal == "SELL" and "BUY" in raw_signal:
        risk_flags.append("TECH_SENTIMENT_CONFLICT")
    if sent_signal == "BUY" and "SELL" in raw_signal:
        risk_flags.append("TECH_SENTIMENT_CONFLICT")

    # ── Confidence tier ──────────────────────────────────────────────────────
    abs_score = abs(sentiment_score)
    if (abs_score > 0.7 or abs(tech_score) >= 5) and article_count >= 3:
        confidence_label = "HIGH"
        confidence_score = min(0.95, 0.6 + abs_score * 0.35 + article_count * 0.02)
    elif (0.4 <= abs_score <= 0.7 or abs(tech_score) >= 3) and article_count >= 2:
        confidence_label = "MEDIUM"
        confidence_score = min(0.75, 0.4 + abs_score * 0.25 + article_count * 0.02)
    else:
        confidence_label = "LOW"
        confidence_score = min(0.45, 0.2 + abs_score * 0.15)

    if risk_flags:
        confidence_score = max(0.1, confidence_score - 0.05 * len(risk_flags))

    confidence_score = round(confidence_score, 3)

    # Legacy int % field kept for UI compatibility
    confidence_pct = int(confidence_score * 100)

    return {
        # Legacy fields (used by existing UI / scheduler)
        "signal":     raw_signal,
        "confidence": confidence_pct,
        "reasons":    reasons,
        # Extended structured output
        "confidence_label": confidence_label,
        "confidence_score": confidence_score,
        "sentiment_tier":   sent_tier,
        "key_drivers":      reasons[:4],
        "risk_flags":       risk_flags,
        "data_status":      data_status,
        "disclaimer":       DISCLAIMER,
        "signal_timestamp": _now_iso(),
    }


def _fallback_signal(risk_flags: list[str] | None = None) -> dict[str, Any]:
    """Return a safe HOLD fallback when data is missing or an error occurs."""
    return {
        "signal":           "HOLD",
        "confidence":       0,
        "reasons":          ["Insufficient data — pipeline fallback triggered. Do not trade."],
        "confidence_label": "LOW",
        "confidence_score": 0.0,
        "sentiment_tier":   "SENTIMENT_NEUTRAL",
        "key_drivers":      [],
        "risk_flags":       (risk_flags or []) + ["DATA_MISSING", "PIPELINE_FALLBACK"],
        "data_status":      "FALLBACK",
        "disclaimer":       DISCLAIMER,
        "signal_timestamp": _now_iso(),
    }
