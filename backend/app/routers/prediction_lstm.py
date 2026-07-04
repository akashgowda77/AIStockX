"""LSTM prediction router.

Phase 12 goal:
- Add POST/GET endpoints for LSTM training + prediction.
- Keep response format consistent with Linear Regression router.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from ..services.prediction_engine import PredictionEngine


router = APIRouter(prefix="/api/prediction", tags=["prediction"])


@router.post("/lstm/train/{symbol}")
def train_lstm(symbol: str, force_retrain: bool = Query(False)) -> Dict[str, Any]:
    """Train or load LSTM model and return prediction."""

    engine = PredictionEngine()
    try:
        # PredictionEngine already returns standardized payload.
        return engine.train(symbol=symbol, model_name="lstm", force_retrain=force_retrain)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/lstm/{symbol}")
def predict_lstm(symbol: str) -> Dict[str, Any]:
    """Predict next-day close using saved LSTM model."""

    engine = PredictionEngine()
    try:
        return engine.predict(symbol=symbol, model_name="lstm")
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

