"""LSTM forecasting model (next-day close).

Phase 12 goal:
- Train a Keras LSTM model for next-day stock closing price prediction.
- Reuse the shared prediction pipeline, metrics, train/test split and model manager.

Improvements:
- Proper scaler persistence
- Consistent sequence generation
- EarlyStopping
- Reproducible training
- Better metadata
- Robust validation
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras import layers

from .base_model import BaseModel
from .metrics import all_metrics
from .model_manager import ModelManager
from .train_test import split_dataset
from ..services.prediction_pipeline import prepare_prediction_data


# ---------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------

np.random.seed(42)
random.seed(42)
tf.random.set_seed(42)


@dataclass
class LSTMPredictionResult:
    """Prediction result returned by the LSTM model."""

    predicted_price: float
    actual_price: Optional[float]
    error: Optional[float]
    confidence_score: float
    metrics: Dict[str, float]


class LSTMModel(BaseModel):
    """LSTM model for next-day stock prediction."""

    def __init__(self, symbol: str) -> None:

        self.symbol = symbol

        self.model_manager = ModelManager()

        self._model_prefix = f"lstm_{symbol}"

        self.model: Optional[keras.Model] = None

        self.feature_columns: List[str] = []

        self.training_rows = 0

        self.metrics_: Dict[str, float] = {}

        self.lookback = 10

        self.epochs = 50

        self.batch_size = 16

        self.x_scaler = MinMaxScaler()

        self.y_scaler = MinMaxScaler()

    def model_name(self) -> str:
        return "LSTM"

    # -------------------------------------------------------------
    # Paths
    # -------------------------------------------------------------

    def _metadata_path(self) -> str:

        return os.path.join(
            self.model_manager.model_dir,
            f"{self._model_prefix}.json",
        )

    def _keras_model_path(self) -> str:

        return os.path.join(
            self.model_manager.model_dir,
            f"{self._model_prefix}.keras",
        )

    def _x_scaler_path(self) -> str:

        return os.path.join(
            self.model_manager.model_dir,
            f"{self._model_prefix}_x_scaler.joblib",
        )

    def _y_scaler_path(self) -> str:

        return os.path.join(
            self.model_manager.model_dir,
            f"{self._model_prefix}_y_scaler.joblib",
        )

    # -------------------------------------------------------------
    # Sequence Builder
    # -------------------------------------------------------------

    def _create_sequences(
        self,
        X: np.ndarray,
        y: np.ndarray,
        lookback: int,
    ) -> Tuple[np.ndarray, np.ndarray]:

        X_sequences = []
        y_sequences = []

        for i in range(lookback, len(X)):
            X_sequences.append(
                X[i - lookback:i]
            )
            y_sequences.append(
                y[i]
            )

        return (
            np.asarray(X_sequences),
            np.asarray(y_sequences),
        )

    # -------------------------------------------------------------
    # Data Preparation
    # -------------------------------------------------------------

    def prepare_data(
        self,
        df: Optional[pd.DataFrame] = None,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:

        payload = prepare_prediction_data(
            self.symbol,
            period="1y",
            interval="1d",
        )

        full_df = payload["dataframe"]

        self.feature_columns = payload["feature_columns"]

        self.training_rows = int(payload["metadata"]["rows"])

        missing = [
            column
            for column in self.feature_columns
            if column not in full_df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing feature columns: {missing}"
            )

        X = (
            full_df[self.feature_columns]
            .astype(float)
            .values
        )

        y = (
            full_df[payload["target_column"]]
            .astype(float)
            .values
        )

        minimum_rows = (self.lookback * 3) + 20

        if len(X) < minimum_rows:
            raise ValueError(
                f"Need at least {minimum_rows} rows for LSTM training."
            )

        return (
            X,
            y,
            self.feature_columns,
        )

    # -------------------------------------------------------------
    # Model
    # -------------------------------------------------------------

    def _build_model(
        self,
        feature_count: int,
    ) -> keras.Model:

        model = keras.Sequential([
            layers.Input(
                shape=(
                    self.lookback,
                    feature_count,
                )
            ),

            layers.LSTM(
                units=64,
                return_sequences=True,
            ),

            layers.Dropout(0.2),

            layers.LSTM(32),

            layers.Dropout(0.2),

            layers.Dense(
                16,
                activation="relu",
            ),

            layers.Dense(1),
        ])

        model.compile(
            optimizer="adam",
            loss="mse",
        )

        return model
        # -------------------------------------------------------------
    # Training
    # -------------------------------------------------------------

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> None:

        X_train_raw, X_test_raw, y_train_raw, y_test_raw = split_dataset(
            X,
            y,
            test_ratio=0.2,
        )

        # Fit scalers ONLY on training data
        self.x_scaler.fit(X_train_raw)
        self.y_scaler.fit(y_train_raw.reshape(-1, 1))

        X_train_scaled = self.x_scaler.transform(X_train_raw)
        X_test_scaled = self.x_scaler.transform(X_test_raw)

        y_train_scaled = (
            self.y_scaler
            .transform(y_train_raw.reshape(-1, 1))
            .reshape(-1)
        )

        y_test_scaled = (
            self.y_scaler
            .transform(y_test_raw.reshape(-1, 1))
            .reshape(-1)
        )

        # Build sequences
        X_train_seq, y_train_seq = self._create_sequences(
            X_train_scaled,
            y_train_scaled,
            self.lookback,
        )

        # Build test sequences using the last lookback rows from training
        X_test_combined = np.concatenate(
            [
                X_train_scaled[-self.lookback:],
                X_test_scaled,
            ],
            axis=0,
        )

        y_test_combined = np.concatenate(
            [
                y_train_scaled[-self.lookback:],
                y_test_scaled,
            ],
            axis=0,
        )

        X_test_seq, y_test_seq = self._create_sequences(
            X_test_combined,
            y_test_combined,
            self.lookback,
        )

        if len(X_train_seq) == 0:
            raise ValueError(
                "Training sequence generation failed."
            )

        if len(X_test_seq) == 0:
            raise ValueError(
                "Testing sequence generation failed."
            )

        feature_count = X_train_seq.shape[2]

        self.model = self._build_model(
            feature_count,
        )

        callback = keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            min_delta=1e-4,
            restore_best_weights=True,
        )

        self.model.fit(
            X_train_seq,
            y_train_seq,
            validation_split=0.1,
            epochs=self.epochs,
            batch_size=self.batch_size,
            callbacks=[callback],
            shuffle=False,
            verbose=0,
        )

        # Evaluate

        y_pred_scaled = (
            self.model
            .predict(
                X_test_seq,
                verbose=0,
            )
            .reshape(-1)
        )

        y_pred = (
            self.y_scaler
            .inverse_transform(
                y_pred_scaled.reshape(-1, 1)
            )
            .reshape(-1)
        )

        y_true = (
            self.y_scaler
            .inverse_transform(
                y_test_seq.reshape(-1, 1)
            )
            .reshape(-1)
        )

        self.metrics_ = all_metrics(
            y_true=y_true,
            y_pred=y_pred,
        )

    # -------------------------------------------------------------
    # Prediction
    # -------------------------------------------------------------

    def predict(
        self,
        X: np.ndarray,
    ) -> np.ndarray:

        if self.model is None:
            raise RuntimeError(
                "LSTM model has not been loaded."
            )

        if len(X) < self.lookback:
            raise ValueError(
                "Not enough rows for prediction."
            )

        recent_window = X[-self.lookback :]

        X_scaled = self.x_scaler.transform(
            recent_window.astype(float)
        )

        X_input = X_scaled.reshape(
            1,
            self.lookback,
            len(self.feature_columns),
        )

        prediction_scaled = self.model.predict(
            X_input,
            verbose=0,
        )

        prediction = self.y_scaler.inverse_transform(
            prediction_scaled
        )

        return prediction.reshape(-1)

    # -------------------------------------------------------------
    # Evaluation
    # -------------------------------------------------------------

    def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Dict[str, float]:

        return dict(self.metrics_)
    
        # -------------------------------------------------------------
    # Save Model
    # -------------------------------------------------------------

    def save_model(self) -> None:

        if self.model is None:
            raise RuntimeError(
                "No trained LSTM model available."
            )

        os.makedirs(
            self.model_manager.model_dir,
            exist_ok=True,
        )
        
        # Save keras model (.keras format)
        self.model.save(
            self._keras_model_path()
        )

        # Save fitted scalers
        joblib.dump(
            self.x_scaler,
            self._x_scaler_path(),
        )

        joblib.dump(
            self.y_scaler,
            self._y_scaler_path(),
        )

        metadata = {
            "model_name": self.model_name(),
            "symbol": self.symbol,
            "trained_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "training_rows": int(
                self.training_rows
            ),
            "training_samples": int(
                self.training_rows
            ),
            "feature_count": len(
                self.feature_columns
            ),
            "features": self.feature_columns,
            "lookback": self.lookback,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "metrics": self.metrics_,
        }

        with open(
            self._metadata_path(),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                metadata,
                f,
                indent=4,
            )

    # -------------------------------------------------------------
    # Load Model
    # -------------------------------------------------------------

    def load_model(self) -> None:

        if not os.path.exists(
            self._keras_model_path()
        ):
            raise FileNotFoundError(
                "Saved LSTM model not found."
            )

        self.model = keras.models.load_model(
            self._keras_model_path()
        )

        if not os.path.exists(
            self._metadata_path()
        ):
            raise FileNotFoundError(
                "Metadata file not found."
            )

        with open(
            self._metadata_path(),
            "r",
            encoding="utf-8",
        ) as f:
            metadata = json.load(f)

        if metadata.get("symbol") != self.symbol:
            raise RuntimeError(
                "Model metadata does not belong to this symbol."
            )

        self.feature_columns = metadata.get(
            "features",
            [],
        )

        self.training_rows = metadata.get(
            "training_rows",
            0,
        )

        self.lookback = metadata.get(
            "lookback",
            14,
        )

        self.epochs = metadata.get(
            "epochs",
            50,
        )

        self.batch_size = metadata.get(
            "batch_size",
            16,
        )

        self.metrics_ = metadata.get(
            "metrics",
            {},
        )

        # Restore scalers
        self.x_scaler = joblib.load(
            self._x_scaler_path()
        )

        self.y_scaler = joblib.load(
            self._y_scaler_path()
        )

    # -------------------------------------------------------------
    # Confidence Score
    # -------------------------------------------------------------

    def _confidence_score(self) -> float:

        accuracy = self.metrics_.get(
            "prediction_accuracy_percent",
            0.0,
        )

        return float(
            max(
                0.0,
                min(
                    100.0,
                    accuracy,
                ),
            )
        )

    # -------------------------------------------------------------
    # Train or Load
    # -------------------------------------------------------------

    def train_or_load(
        self,
        force_retrain: bool = False,
    ) -> None:
        """Train the model or load an existing one."""

        if (
            not force_retrain
            and os.path.exists(self._keras_model_path())
            and os.path.exists(self._metadata_path())
        ):
            self.load_model()
            return

        X, y, _ = self.prepare_data()

        self.train(
            X,
            y,
        )

        self.save_model()

        # -------------------------------------------------------------
    # Predict Next Close
    # -------------------------------------------------------------

    def predict_next_close(
        self,
    ) -> LSTMPredictionResult:
        """Predict the next trading day's closing price."""

        if self.model is None:
            raise RuntimeError(
                "LSTM model has not been loaded."
            )

        payload = prepare_prediction_data(
            self.symbol,
            period="1y",
            interval="1d",
        )

        df = payload["dataframe"]

        if df.empty:
            raise ValueError(
                "Prediction dataset is empty."
            )

        feature_columns = payload["feature_columns"]
        target_column = payload["target_column"]

        missing = [
            column
            for column in feature_columns
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing feature columns: {missing}"
            )

        latest_features = (
            df[feature_columns]
            .astype(float)
            .values
        )

        if len(latest_features) < self.lookback:
            raise ValueError(
                f"Need at least {self.lookback} rows for prediction."
            )

        # ---------------------------------------------------------
        # Latest lookback window
        # ---------------------------------------------------------

        recent_window = latest_features[-self.lookback :]

        X_scaled = self.x_scaler.transform(
            recent_window
        )

        X_input = X_scaled.reshape(
            1,
            self.lookback,
            len(self.feature_columns),
        )

        prediction_scaled = self.model.predict(
            X_input,
            verbose=0,
        )

        prediction = self.y_scaler.inverse_transform(
            prediction_scaled
        )

        predicted_price = float(
            prediction[0][0]
        )

        # ---------------------------------------------------------
        # Actual value (available only for evaluation)
        # ---------------------------------------------------------

        actual_price: Optional[float] = None
        error: Optional[float] = None

        if (
            target_column in df.columns
            and not pd.isna(
                df.iloc[-1][target_column]
            )
        ):
            actual_price = float(
                df.iloc[-1][target_column]
            )

            error = actual_price - predicted_price

        return LSTMPredictionResult(
            predicted_price=predicted_price,
            actual_price=actual_price,
            error=error,
            confidence_score=self._confidence_score(),
            metrics=dict(self.metrics_),
        )