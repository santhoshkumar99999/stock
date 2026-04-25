from __future__ import annotations

from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def label_sentiment(score: float) -> str:
    if score > 0.05:
        return "Bullish"
    if score < -0.05:
        return "Bearish"
    return "Neutral"


def score_articles(articles: list[dict[str, Any]]) -> dict[str, Any]:
    if not articles:
        return {"sentiment": "Neutral", "score": 0.0, "articles": []}
    scored = []
    values = []
    for article in articles:
        text = f"{article.get('title', '')}. {article.get('summary', '')}"
        comp = analyzer.polarity_scores(text)["compound"]
        article_out = dict(article)
        article_out["score"] = comp
        article_out["sentiment"] = label_sentiment(comp)
        scored.append(article_out)
        values.append(comp)
    avg = sum(values) / len(values)
    return {"sentiment": label_sentiment(avg), "score": avg, "articles": scored}
