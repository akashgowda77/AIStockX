"""Model manager.

Responsible for:
- Creating the model directory
- Checking if a model already exists
- Saving/loading sklearn models with joblib

For LSTM later:
- TensorFlow save() will be added in the future.
"""

from __future__ import annotations

import os
from typing import Optional

import joblib
from pathlib import Path

class ModelManager:
    """Handle saving/loading models for each model name."""

    

    def __init__(self, model_dir: str | None = None) -> None:
        if model_dir is None:
            self.model_dir = Path(__file__).resolve().parent / "saved_models"
        else:
            self.model_dir = Path(model_dir)

        self.model_dir.mkdir(parents=True, exist_ok=True)

    def _model_path(self, model_name: str) -> str:
        """Create the absolute file path for a model."""

        safe_name = (
            model_name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        return str(self.model_dir / f"{safe_name}.joblib")

    def model_exists(self, model_name: str) -> bool:
        """Return True if a saved model exists."""

        return os.path.exists(self._model_path(model_name))

    def save_sklearn_model(self, model, model_name: str) -> str:
        """Save a sklearn-like model using joblib.

        Input:
            model: trained estimator
            model_name: model name for file naming
        Output:
            path where model was saved
        """

        path = self._model_path(model_name)
        try:
            joblib.dump(model, path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to save model: {exc}"
            )
        return path

    def load_sklearn_model(self, model_name: str):
        """Load a previously saved sklearn model.

        Input:
            model_name
        Output:
            loaded estimator
        """

        path = self._model_path(model_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")

        try:
            return joblib.load(path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load model: {exc}"
            )

    def metadata_path(self, model_name: str) -> str:
        """Return metadata JSON path."""

        safe_name = (
            model_name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        return str(self.model_dir / f"{safe_name}.json")