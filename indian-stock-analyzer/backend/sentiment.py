from __future__ import annotations

from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def label_sentiment(score: float) -> str:
    """
    Map compound score to a sentiment label.
    Uses the same thresholds as the signal decision matrix.
    """
    if score >= 0.6:
        return "Bullish"       # strong positive → eligible for BUY signal
    if score >= 0.2:
        return "Bullish"       # weak positive → will be caught as HOLD in matrix
    if score <= -0.6:
        return "Bearish"       # strong negative → eligible for SELL signal
    if score <= -0.2:
        return "Bearish"       # weak negative → HOLD in matrix
    return "Neutral"


def _sentiment_label_simple(score: float) -> str:
    """Legacy single-word label for API display."""
    if score > 0.05:
        return "Bullish"
    if score < -0.05:
        return "Bearish"
    return "Neutral"


def score_articles(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Score a list of news articles using VADER sentiment analysis.
    Returns:
        {
            "sentiment": str,      # Bullish | Bearish | Neutral
            "score": float,        # average compound score [-1, +1]
            "article_count": int,
            "articles": list[dict] # each article with score + sentiment
        }
    """
    if not articles:
        return {
            "sentiment":     "Neutral",
            "score":         0.0,
            "article_count": 0,
            "articles":      [],
        }

    scored: list[dict[str, Any]] = []
    values: list[float] = []

    for article in articles:
        text = f"{article.get('title', '')}. {article.get('summary', '')}"
        comp = analyzer.polarity_scores(text)["compound"]
        article_out = dict(article)
        article_out["score"] = round(comp, 4)
        article_out["sentiment"] = _sentiment_label_simple(comp)
        scored.append(article_out)
        values.append(comp)

    avg = sum(values) / len(values)
    label = label_sentiment(avg)

    # Detect contradictory signals (high std dev)
    if len(values) >= 2:
        mean = avg
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        if std_dev > 0.4:
            label = "Mixed"

    return {
        "sentiment":     label,
        "score":         round(avg, 4),
        "article_count": len(scored),
        "articles":      scored,
    }
