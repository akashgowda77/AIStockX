from __future__ import annotations

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query

from ..services.sentiment_service import SentimentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/{symbol}/sentiment", response_model=Dict[str, Any])
def get_news_sentiment(
    symbol: str,
    count: int = Query(default=10, ge=1, le=50, description="Number of news headlines to fetch & analyze")
):
    """
    Fetch real-time financial news headlines for a stock symbol and compute FinBERT sentiment analysis.

    Returns:
    - overall_sentiment_score: float in [-1.0 (Bearish), +1.0 (Bullish)]
    - overall_sentiment_label: 'Bullish' | 'Bearish' | 'Neutral'
    - sentiment_distribution: count of bullish, bearish, and neutral news
    - news: list of analyzed headlines with FinBERT confidence & scores
    """
    try:
        return SentimentService.get_stock_news_sentiment(symbol, count=count)
    except Exception as exc:
        logger.error("Failed to compute news sentiment for %s: %s", symbol, exc)
        raise HTTPException(status_code=500, detail=f"Failed to fetch news sentiment for '{symbol}'.")
