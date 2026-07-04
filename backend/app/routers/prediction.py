"""Prediction router.

Phase 9 goal:
- Train Linear Regression model (or load existing)
- Predict next close

Endpoints:
POST /api/prediction/linear/train/{symbol}
GET /api/prediction/linear/{symbol}
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query


from ..services.prediction_engine import PredictionEngine
from ..services.stock_service import validate_symbol



router = APIRouter(prefix="/prediction", tags=["prediction"])




def ok(data: Any, message: str) -> Dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def error(message: str) -> Dict[str, Any]:
    return {"success": False, "message": message, "data": None}


@router.post("/linear/train/{symbol}")
def train_linear(symbol: str, force_retrain: bool = Query(False)) -> Dict[str, Any]:
    """Train or load a model and return next-day prediction (via PredictionEngine)."""

    engine = PredictionEngine()
    try:
        return engine.train(symbol=symbol, model_name="linear", force_retrain=force_retrain)


    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/linear/{symbol}")
def predict_linear(symbol: str) -> Dict[str, Any]:
    """Predict next close using loaded model (via PredictionEngine)."""

    engine = PredictionEngine()
    try:
        return engine.predict(symbol=symbol, model_name="linear")
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/compare/{symbol}")
def compare_models(symbol: str) -> Dict[str, Any]:
    """Compare Linear Regression and LSTM predictions."""

    engine = PredictionEngine()

    try:
        return engine.compare_models(symbol)

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )