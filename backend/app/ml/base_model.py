"""Base ML model interface (beginner-friendly).

All future ML models (Linear Regression, LSTM, etc.) must inherit from BaseModel.

We keep this simple on purpose:
- ABC defines the required methods.
- Concrete models can plug in their own training/prediction logic.

Methods are documented with inputs/outputs, but actual behavior depends on the child class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import pandas as pd


class BaseModel(ABC):
    """Abstract base class for prediction models."""

    @abstractmethod
    def prepare_data(self, df: pd.DataFrame) -> Tuple[Any, Any]:
        """Convert raw dataframe into (X, y) suitable for the model.

        Input:
            df: raw or cleaned stock dataframe
        Output:
            (X, y): model-specific feature/target structures
        """

    @abstractmethod
    def train(self, X: Any, y: Any) -> None:
        """Train the model.

        Input:
            X: features
            y: targets
        Output:
            None
        """

    @abstractmethod
    def predict(self, X: Any) -> Any:
        """Generate predictions.

        Input:
            X: features
        Output:
            predictions (type depends on model)
        """

    @abstractmethod
    def save_model(self) -> None:
        """Persist the trained model to disk."""

    @abstractmethod
    def load_model(self) -> bool:
        """Load a previously saved model from disk."""

    @abstractmethod
    def evaluate(self, X: Any, y: Any) -> Dict[str, float]:
        """Evaluate model predictions and return metrics.

        Input:
            X: features
            y: targets
        Output:
            metrics dict
        """

    def model_name(self) -> str:
        """Return a model name used for saving/loading."""

        return self.__class__.__name__

    
    @property
    def name(self) -> str:
        return self.__class__.__name__