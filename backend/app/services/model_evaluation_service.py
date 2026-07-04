"""Model evaluation service.

Phase 10 goal:
Provide reusable APIs for viewing model performance and metadata.

Responsibilities:
- Read saved model metadata JSON
- Return metrics, features, trained timestamp, version info
- Return whether a model exists

How metadata is stored:
- Each trained model saves a .joblib file under `backend/app/ml/saved_models/`.
- The Linear Regression model also saves a sidecar JSON file with the same base name
  (e.g., linear_regression_AAPL.joblib and linear_regression_AAPL.json).

Why metadata is useful:
- FastAPI can display model metrics without loading the model for inference.
- Frontend can show model accuracy comparisons.

How it supports multiple models later:
- The service works by scanning metadata files and using model name
  conventions in the JSON. LSTM will produce similar JSON, so endpoints remain stable.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from pathlib import Path

@dataclass
class ModelMetaPaths:
    model_dir: str


class ModelEvaluationService:
    """Read metadata JSON files saved next to trained models."""

    def __init__(self, model_dir: str | None = None) -> None:
        if model_dir is None:
            self.model_dir = str(
                Path(__file__).resolve().parents[1]
                / "ml"
                / "saved_models"
            )
        else:
            self.model_dir = model_dir

        os.makedirs(self.model_dir, exist_ok=True)

    def _safe_model_base(self, model_name: str, symbol: str) -> str:
        """Build consistent metadata base name.

        Input:
            model_name: e.g. 'Linear Regression'
            symbol: ticker
        Output:
            base string used to locate JSON

        Note:
            Currently, Linear Regression model names are created as:
            linear_regression_{symbol}
        """

        model_key = model_name.lower().replace(" ", "_")
        if "linear_regression" not in model_key:
            # For now we only support linear regression metadata naming.
            # LSTM later will follow same approach.
            pass

        # Map human readable name -> internal saved model prefix
        if model_name.strip().lower() in {"linear regression", "linear_regression"}:
            return f"linear_regression_{symbol}"

        return f"{model_key}_{symbol}"

    def _metadata_path(self, model_base: str) -> str:
        return os.path.join(self.model_dir, f"{model_base}.json")

    def model_exists(self, model_name: str, symbol: str) -> bool:
        """Return whether metadata exists for the given model+symbol."""
        model_base = self._safe_model_base(model_name=model_name, symbol=symbol)
        path = self._metadata_path(model_base)
        return os.path.exists(path)

    def list_models(self) -> List[Dict[str, Any]]:
        """Return all available trained model metadata."""
        results: List[Dict[str, Any]] = []
        for fname in os.listdir(self.model_dir):
            if not fname.endswith(".json"):
                continue
            full_path = os.path.join(self.model_dir, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                results.append(meta)
            except Exception:
                # Skip invalid JSON files.
                continue
        return results

    def get_model_metadata(self, model_name: str, symbol: str) -> Dict[str, Any]:
        """Read metadata JSON for a given model+symbol."""

        model_base = self._safe_model_base(model_name=model_name, symbol=symbol)
        path = self._metadata_path(model_base)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Model metadata not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # Add model_exists boolean to response.
        meta["exists"] = True
        return meta

    def get_features(self, model_name: str, symbol: str) -> List[str]:
        """Return feature list from metadata."""
        meta = self.get_model_metadata(model_name=model_name, symbol=symbol)
        return list(meta.get("features", []))

    def get_training_timestamp(self, model_name: str, symbol: str) -> Optional[str]:
        """Return the trained_at ISO timestamp from metadata."""
        meta = self.get_model_metadata(model_name=model_name, symbol=symbol)
        return meta.get("trained_at")

    def get_model_version_info(self, model_name: str, symbol: str) -> Dict[str, Any]:
        """Return model version information.

        For now, metadata does not explicitly store a version.
        We provide a simple placeholder structure.
        """

        meta = self.get_model_metadata(model_name=model_name, symbol=symbol)
        trained_at = meta.get("trained_at")
        version_hash = str(hash((model_name, symbol, trained_at)))
        return {
            "version": "v1",
            "version_hash": version_hash,
        }

    def get_model_evaluation_summary(self, model_name: str, symbol: str) -> Dict[str, Any]:
        """Return a standardized summary for API responses."""

        meta = self.get_model_metadata(model_name=model_name, symbol=symbol)
        metrics = meta.get("metrics", {})

        # Confidence score in this project currently isn't stored in metadata.
        # Keep it in the response using a best-effort heuristic if rmse exists.
        rmse_val = metrics.get("rmse")
        confidence_score = None
        if rmse_val is not None:
            confidence_score = max(0.0, min(100.0, 100.0 - float(rmse_val) * 0.1))

        version_info = self.get_model_version_info(model_name=model_name, symbol=symbol)

        return {
            "model_name": meta.get("model_name", model_name),
            "symbol": meta.get("symbol", symbol),
            "trained_at": meta.get("trained_at"),
            "version": version_info.get("version"),
            "version_hash": version_info.get("version_hash"),
            "features": list(meta.get("features", [])),
            "metrics": metrics,
            "confidence_score": confidence_score,
        }

