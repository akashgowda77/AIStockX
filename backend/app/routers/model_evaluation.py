"""Model evaluation router.

Phase 10 goal:
Provide APIs for viewing model performance and metadata.

Endpoints:
- GET /api/models
- GET /api/models/{symbol}/linear
- GET /api/models/{symbol}/exists
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..services.model_evaluation_service import ModelEvaluationService
from ..services.stock_service import validate_symbol


router = APIRouter(prefix="/api/models", tags=["model-evaluation"])


def ok(data: Any, message: str) -> Dict[str, Any]:
    return {"success": True, "message": message, "data": data}


@router.get("")
def list_models() -> Dict[str, Any]:
    """Return all available trained model metadata."""

    try:
        service = ModelEvaluationService()
        all_meta = service.list_models()
        return ok(all_meta, message="Model metadata list")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{symbol}/linear")
def get_linear_model(symbol: str) -> Dict[str, Any]:
    """Return Linear Regression model metadata and evaluation metrics."""

    try:
        symbol_normalized = validate_symbol(symbol)
        service = ModelEvaluationService()

        if not service.model_exists(model_name="Linear Regression", symbol=symbol_normalized):
            raise HTTPException(status_code=404, detail="Linear Regression model not trained")

        summary = service.get_model_evaluation_summary(model_name="Linear Regression", symbol=symbol_normalized)
        metrics = summary.get("metrics", {})

        # Standard response fields expected by the requirement.
        data = {
            "model_name": summary.get("model_name"),
            "symbol": summary.get("symbol"),
            "training_date": summary.get("trained_at"),
            "features": summary.get("features"),
            "rmse": metrics.get("rmse"),
            "mae": metrics.get("mae"),
            "mape": metrics.get("mape"),
            "r2": metrics.get("r2"),
            "direction_accuracy": metrics.get("direction_accuracy"),
            "prediction_accuracy": metrics.get("prediction_accuracy_percent"),
            "confidence_score": summary.get("confidence_score"),
            "version": summary.get("version"),
            "version_hash": summary.get("version_hash"),
        }

        return ok(data, message="Linear model evaluation loaded")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{symbol}/exists")
def linear_model_exists(symbol: str) -> Dict[str, Any]:
    """Return whether a Linear Regression model is available."""

    try:
        symbol_normalized = validate_symbol(symbol)
        service = ModelEvaluationService()
        exists = service.model_exists(model_name="Linear Regression", symbol=symbol_normalized)
        return ok({"exists": exists}, message="Model existence")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

