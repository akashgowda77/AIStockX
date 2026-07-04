"""Indicators router.

Endpoint:
- GET /api/indicators/{symbol}

Flow:
    Stock Service -> Data Pipeline -> Indicator Service -> JSON Response

Return:
    - Latest indicator values
    - Trend signal (Bullish/Bearish/Neutral)
    - Indicator summary with confidence

No AI/ML here; only simple rule-based logic.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, HTTPException

from ..services.indicator_service import generate_all_indicators
from ..services.stock_service import get_historical_data, validate_symbol
from ..services.data_pipeline import clean_stock_data


router = APIRouter(prefix="/api/indicators", tags=["indicators"])


def to_latest_dict(data: pd.DataFrame, columns) -> Dict[str, Any]:
    """Extract latest (last row) values for given columns."""

    latest = data.iloc[-1]
    result: Dict[str, Any] = {}
    for col in columns:
        val = latest.get(col)
        if pd.isna(val):
            result[col] = None
        else:
            # Convert numpy types to python primitives
            if hasattr(val, "item"):
                result[col] = val.item()
            else:
                result[col] = float(val) if isinstance(val, (int, float)) else val
    return result


def compute_trend_signal(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based trend signal.

    Simple logic (beginner friendly):
    - EMA vs SMA => trend
    - RSI => overbought/oversold
    - MACD histogram => momentum
    - Bollinger => price position

    Output:
        overall_signal + confidence + per-indicator signals
    """

    signals: Dict[str, str] = {}
    confidence_points = 0

    # EMA vs SMA
    ema_20 = indicators.get("ema_20")
    sma_20 = indicators.get("sma_20")
    close = indicators.get("close")

    if ema_20 is not None and sma_20 is not None and close is not None:
        if close > ema_20 and ema_20 > sma_20:
            signals["EMA"] = "Bullish"
            confidence_points += 25
        elif close < ema_20 and ema_20 < sma_20:
            signals["EMA"] = "Bearish"
            confidence_points += 25
        else:
            signals["EMA"] = "Neutral"

    # RSI
    rsi = indicators.get("rsi_14")
    if rsi is not None:
        if rsi >= 70:
            signals["RSI"] = "Bearish"
            confidence_points += 15
        elif rsi <= 30:
            signals["RSI"] = "Bullish"
            confidence_points += 15
        else:
            signals["RSI"] = "Neutral"

    # MACD histogram
    macd_hist = indicators.get("macd_hist")
    if macd_hist is not None:
        if macd_hist > 0:
            signals["MACD"] = "Bullish"
            confidence_points += 20
        elif macd_hist < 0:
            signals["MACD"] = "Bearish"
            confidence_points += 20
        else:
            signals["MACD"] = "Neutral"

    # Bollinger bands
    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    if bb_upper is not None and bb_lower is not None and close is not None:
        if close <= bb_lower:
            signals["Bollinger"] = "Bullish"
            confidence_points += 15
        elif close >= bb_upper:
            signals["Bollinger"] = "Bearish"
            confidence_points += 15
        else:
            signals["Bollinger"] = "Neutral"

    # Compute overall
    bullish = sum(1 for s in signals.values() if s == "Bullish")
    bearish = sum(1 for s in signals.values() if s == "Bearish")

    if bullish > bearish:
        overall = "Bullish"
    elif bearish > bullish:
        overall = "Bearish"
    else:
        overall = "Neutral"

    MAX_POINTS = 75

    confidence = round(
        confidence_points / MAX_POINTS * 100,
        2,
    )

    return {
        "overall_signal": overall,
        "confidence": confidence,
        "signals": signals,
    }


@router.get("/{symbol}")
def get_indicators(symbol: str) -> Dict[str, Any]:
    """Get latest indicator values and a rule-based trend summary."""

    try:
        validate_symbol(symbol)

        # Pull historical OHLC data from stock service
        history_rows = get_historical_data(symbol=symbol, period="1y", interval="1d")

        raw_df = pd.DataFrame(history_rows)
        cleaned_df = clean_stock_data(raw_df)

        # Generate indicators
        enriched = generate_all_indicators(cleaned_df)
        if enriched.empty:
            raise HTTPException(
                status_code=400,
                detail="No indicator data available."
            )
        
        indicator_columns = [
            "close",
            "sma_20",
            "ema_20",
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_hist",
            "bb_middle",
            "bb_upper",
            "bb_lower",
            "atr_14",
            "obv",
            "stoch_k_14",
            "stoch_d_14",
        ]

        latest_values = to_latest_dict(enriched, indicator_columns)
        summary = compute_trend_signal(latest_values)

        return {
            "success": True,
            "message": "Indicators fetched successfully",
            "data": {
                "latest": latest_values,
                "trend": summary,
            },
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

