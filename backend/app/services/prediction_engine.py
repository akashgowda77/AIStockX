"""Prediction engine.

Phase 11 goal:
Centralize prediction logic for all ML models.

Responsibilities:
- Select prediction model by name
- Load existing trained model
- Trigger training if required
- Route prediction requests
- Return standardized prediction responses

Design:
- This layer prevents routers from knowing about specific model classes.
- When LSTM is added later, only this engine will need changes (plus a new model class).

Supported model names:
- 'linear' -> LinearRegressionModel
- 'lstm' -> placeholder (501)
"""

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import HTTPException


from ..ml.linear_regression_model import LinearRegressionModel
from ..ml.lstm_model import LSTMModel
from ..services.stock_service import validate_symbol
from ..services.model_comparison_service import ModelComparisonService


def _ok(data: Any, message: str) -> Dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def _not_implemented(message: str) -> HTTPException:
    return HTTPException(status_code=501, detail=message)


class PredictionEngine:
    """Orchestrate training/loading/prediction for supported models."""

    def predict(self, symbol: str, model_name: str = "linear") -> Dict[str, Any]:
        """Predict next close for a symbol using the selected model."""

        symbol_normalized = validate_symbol(symbol)

        normalized = model_name.strip().lower() if model_name else "linear"

        if normalized == "linear":
            model = LinearRegressionModel(symbol=symbol_normalized)

            # If model doesn't exist, communicate clearly.
            if not model.model_manager.model_exists(model._model_name):
                raise HTTPException(status_code=404, detail="Model not trained yet")

            model.load_model()
            prediction = model.predict_next_close(include_actual=True)

            return _ok(
                data={
                    "model": model.model_name(),
                    "symbol": symbol_normalized,
                    "prediction": {
                        "predicted_price": prediction.predicted_price,
                        "actual_price": prediction.actual_price,
                        "error": prediction.error,
                        "confidence_score": prediction.confidence_score,
                    },
                    "metrics": prediction.metrics,
                },
                message="Prediction generated",
            )

        if normalized == "lstm":
            model = LSTMModel(symbol=symbol_normalized)

            if not os.path.exists(model._keras_model_path()):
                raise HTTPException(
                    status_code=404,
                    detail="LSTM model not trained yet",
                )

            model.load_model()
            prediction = model.predict_next_close()

            return _ok(
                data={
                    "model": model.model_name(),
                    "symbol": symbol_normalized,
                    "prediction": {
                        "predicted_price": prediction.predicted_price,
                        "actual_price": prediction.actual_price,
                        "error": prediction.error,
                        "confidence_score": prediction.confidence_score,
                    },
                    "metrics": prediction.metrics,
                },
                message="Prediction generated",
            )


        raise HTTPException(status_code=400, detail=f"Unsupported model_name: {model_name}")

    def train(self, symbol: str, model_name: str = "linear", force_retrain: bool = False) -> Dict[str, Any]:
        """Train or load and then return a prediction for the next close."""
        print("========== PREDICTION ENGINE LOADED ==========")
        print("Model name received:", model_name)
        
        symbol_normalized = validate_symbol(symbol)
        normalized = model_name.strip().lower() if model_name else "linear"
        print("normalized =", repr(normalized))
        if normalized == "linear":
            model = LinearRegressionModel(symbol=symbol_normalized)
            model.train_or_load(force_retrain=force_retrain)
            
            prediction = model.predict_next_close(include_actual=True)
            # Reuse same prediction payload structure.
            return _ok(
                data={
                    "model": model.model_name(),
                    "symbol": symbol_normalized,
                    "metrics": prediction.metrics,
                    "prediction": {
                        "predicted_price": prediction.predicted_price,
                        "actual_price": prediction.actual_price,
                        "error": prediction.error,
                        "confidence_score": prediction.confidence_score,
                    },
                },
                message="Training completed (or existing model loaded)",
            )

        if normalized == "lstm":
            print(">>> ENTERED LSTM BLOCK <<<")
            model = LSTMModel(symbol=symbol_normalized)

            try:
                model.train_or_load(force_retrain=force_retrain)
                prediction = model.predict_next_close()

            except Exception as e:
                import traceback
                print("=" * 80)
                print("LSTM TRAINING FAILED")
                print("Exception type:", type(e).__name__)
                print("Exception:", e)
                traceback.print_exc()
                print("=" * 80)
                raise

            return _ok(
                data={
                    "model": model.model_name(),
                    "symbol": symbol_normalized,
                    "metrics": prediction.metrics,
                    "prediction": {
                        "predicted_price": prediction.predicted_price,
                        "actual_price": prediction.actual_price,
                        "error": prediction.error,
                        "confidence_score": prediction.confidence_score,
                    },
                },
                message="Training completed",
            )    


        raise HTTPException(status_code=400, detail=f"Unsupported model_name: {model_name}")

    def compare_models(self, symbol: str) -> Dict[str, Any]:
        """Compare all available prediction models for a stock."""

        symbol_normalized = validate_symbol(symbol)

        service = ModelComparisonService()

        comparison = service.compare(symbol_normalized)

        return _ok(
            data=comparison,
            message="Model comparison generated successfully",
        )