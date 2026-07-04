"""Linear Regression forecasting model.

Phase 9 goal:
- Train a scikit-learn LinearRegression model to predict next day's close.
- Reuse shared ML infrastructure:
  - Prediction pipeline (dataset preparation)
  - train_test.py (chronological splitting)
  - metrics.py (evaluation)
  - model_manager.py (saving/loading)

This file intentionally keeps logic straightforward for interview explanation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .base_model import BaseModel
from .metrics import all_metrics
from .model_manager import ModelManager
from .train_test import split_dataset
from ..services.prediction_pipeline import prepare_prediction_data


@dataclass
class LinearPredictionResult:
    """Result container for predictions."""

    predicted_price: float
    actual_price: Optional[float]
    error: Optional[float]
    confidence_score: float
    metrics: Dict[str, float]


class LinearRegressionModel(BaseModel):
    """Concrete Linear Regression model."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.model_manager = ModelManager()
        self.model: Optional[LinearRegression] = None

        self.feature_columns: List[str] = []
        self.training_rows: int = 0
        self.metrics_: Dict[str, float] = {}

        # model naming in the save folder
        self._model_name = f"linear_regression_{symbol}"

    def _metadata_path(self) -> str:
        """Metadata file path saved beside the model."""

        return self.model_manager._model_path(self._model_name).replace(".joblib", ".json")

    def model_name(self) -> str:
        return "Linear Regression"

    def prepare_data(self, df: pd.DataFrame = None) -> Tuple[np.ndarray, np.ndarray, List[str]]:  # type: ignore[override]
        """Prepare X/y from Prediction Pipeline.

        Input:
            df: unused (Prediction pipeline downloads and prepares data)
        Output:
            X (numpy), y (numpy), feature_columns
        """

        payload = prepare_prediction_data(self.symbol)
        full_df = payload["dataframe"]
        self.feature_columns = payload["feature_columns"]
        self.training_rows = int(payload["metadata"]["rows"])

        missing = [
            col
            for col in self.feature_columns
            if col not in full_df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing feature columns: {missing}"
            )

        # Target column exists in prepare_prediction_data
        X = full_df[self.feature_columns].values
        y = full_df[payload["target_column"]].values

        return X, y, self.feature_columns

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train LinearRegression model.

        Input:
            X: features
            y: target close
        Output:
            None
        """

        self.model = LinearRegression()
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict next close.

        Input:
            X: 2D array of features (n_samples, n_features)
        Output:
            predictions array
        """

        if self.model is None:
            raise RuntimeError("Model is not loaded/trained")

        return self.model.predict(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model on given test set.

        Input:
            X: test features
            y: test targets
        Output:
            metrics dict
        """

        y_pred = self.predict(X)
        metrics = all_metrics(y_true=y, y_pred=y_pred)
        self.metrics_ = metrics
        return metrics

    def save_model(self) -> None:
        """Save model and metadata.

        Input: trained `self.model`
        Output: None
        """

        if self.model is None:
            raise RuntimeError("No model to save")

        # Save joblib model
        self.model_manager.save_sklearn_model(self.model, self._model_name)

        # Save metadata JSON next to the model
        now = datetime.now(timezone.utc).isoformat()

        metadata: Dict[str, Any] = {
            "model_name": self.model_name(),
            "symbol": self.symbol,
            "trained_at": now,
            "training_rows": int(self.training_rows),
            "features": list(self.feature_columns),
            "metrics": self.metrics_,
            "feature_count": len(self.feature_columns),
        }

        with open(self._metadata_path(), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_model(self) -> None:
        """
        Load a previously saved model and its metadata.
        """

        self.model = self.model_manager.load_sklearn_model(
            self._model_name
        )

        metadata: Dict[str, Any] = {}

        try:
            with open(
                self._metadata_path(),
                "r",
                encoding="utf-8",
            ) as f:
                metadata = json.load(f)

            if metadata.get("symbol") != self.symbol:
                raise RuntimeError(
                    "Loaded model metadata does not match symbol."
                )

            self.feature_columns = metadata.get(
                "features",
                [],
            )

            self.training_rows = int(
                metadata.get(
                    "training_rows",
                    0,
                )
            )

            self.metrics_ = metadata.get(
                "metrics",
                {},
            )

        except FileNotFoundError:
            # Model exists but metadata is missing.
            self.feature_columns = []
            self.training_rows = 0
            self.metrics_ = {}

        except Exception:
            raise

    def _confidence_from_rmse(self, rmse_val: float) -> float:
        """Create a simple confidence score from RMSE.

        Heuristic:
        - Normalize by using a typical price scale from training metrics.
        - Keep it beginner-friendly.
        """

        # If rmse is very large, confidence should drop.
        # Confidence = 100 - rmse scaled
        accuracy = self.metrics_.get(
            "prediction_accuracy_percent",
            0.0,
        )

        return float(max(0.0, min(100.0, accuracy)))

    def train_or_load(self, force_retrain: bool = False) -> None:
        """Train if needed; otherwise load an existing model."""

        if not force_retrain and self.model_manager.model_exists(self._model_name):
            self.load_model()
            return

        # Prepare dataset
        X, y, _ = self.prepare_data()

        if len(X) < 30:
            raise ValueError(
                f"Not enough data to train model for {self.symbol}"
            )
        
        # Chronological split
        X_train, X_test, y_train, y_test = split_dataset(X, y, test_ratio=0.2)

        # Train
        self.train(X_train, y_train)

        # Evaluate on test
        self.evaluate(X_test, y_test)

        # Save trained artifacts
        self.save_model()

    def predict_next_close(self, include_actual: bool = True) -> LinearPredictionResult:
        """Predict next trading day close.

        Input:
            include_actual: if True, actual price is taken from the last target row.
        Output:
            LinearPredictionResult
        """

        # Prepare dataset again to get latest feature row + actual target if available.
        payload = prepare_prediction_data(self.symbol)
        df = payload["dataframe"]
        feature_columns = payload["feature_columns"]
        target_col = payload["target_column"]

        if df.empty:
            raise ValueError(
                "Prediction dataset is empty."
            )
        
        latest_row = df.iloc[-1]

        # Features for prediction: use latest feature row, but target is already next-day
        X_latest = latest_row[feature_columns].values.reshape(1, -1)
        prediction = self.predict(X_latest)

        if len(prediction) == 0:
            raise RuntimeError("Prediction failed.")

        y_pred = float(prediction[0])

        actual_price: Optional[float] = None
        error: Optional[float] = None

        # In our dataset, the last row has a known target_close_next,
        # but in real trading it won't be known yet.
        # For this project API, we provide it as 'actual when available'.
        if include_actual and target_col in df.columns:
            actual_price = float(latest_row[target_col])
            error = float(actual_price - y_pred)

        # confidence heuristic
        rmse_val = float(self.metrics_.get("rmse", 0.0))
        confidence_score = self._confidence_from_rmse(rmse_val)

        # Provide metrics as last known evaluation metrics
        metrics_out = dict(self.metrics_)
        if not metrics_out:
            # If model was loaded without metadata, compute simple metrics unavailable.
            metrics_out = {}

        return LinearPredictionResult(
            predicted_price=float(y_pred),
            actual_price=actual_price,
            error=error,
            confidence_score=confidence_score,
            metrics=metrics_out,
        )

