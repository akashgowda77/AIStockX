"""Reusable evaluation metrics for ML forecasting.

All metrics are implemented as beginner-friendly functions.

Direction Accuracy:
- Compares the sign of day-to-day movement between prediction and actual.

Prediction Accuracy %:
- Simple percentage based on relative error magnitude.
"""

from __future__ import annotations

from typing import Dict

import numpy as np


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("Empty arrays are not allowed.")
    
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    if len(y_true) == 0:
        raise ValueError("Empty arrays are not allowed.")
    
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error (%).

    Uses a small epsilon to avoid divide-by-zero.
    """
    
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("Empty arrays are not allowed.")
    
    eps = 1e-8
    denom = np.maximum(np.abs(y_true), eps)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of Determination (R²)."""

    

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("Empty arrays are not allowed.")
    
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    return float(1 - ss_res / ss_tot)


def direction_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Direction Accuracy (%): correct up/down movement.

    For forecasting next close:
    direction is inferred from (y - prev_close).

    Since we may not have prev_close here, we approximate direction by comparing
    change relative to previous true value (shifted by 1).
    """
    
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) < 2:
        return 0.0
    
    if len(y_true) == 0:
        raise ValueError("Empty arrays are not allowed.")
    # Approximate previous close as previous actual
    prev_true = y_true[:-1]
    true_change = y_true[1:] - prev_true

    # Align predicted next values with true next values
    pred_change = y_pred[1:] - prev_true

    true_dir = np.sign(true_change)
    pred_dir = np.sign(pred_change)

    acc = np.mean(true_dir == pred_dir) * 100.0
    return float(acc)


def prediction_accuracy_percent(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Prediction Accuracy % based on relative error.

    A simple approach for interviews:
    accuracy = 100 - mean(|error|/|y_true| * 100)
    """

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("Empty arrays are not allowed.")


    eps = 1e-8
    denom = np.maximum(np.abs(y_true), eps)
    rel_error_pct = np.mean(np.abs((y_true - y_pred) / denom)) * 100.0
    acc = max(0.0, min(100.0, 100.0 - rel_error_pct))
    return float(max(acc, 0.0))


def all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Return all metrics in one dictionary."""

    metrics = {
        "rmse": rmse(y_true, y_pred),
        "mae": mae(y_true, y_pred),
        "mape": mape(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
        "direction_accuracy": direction_accuracy(y_true, y_pred),
        "prediction_accuracy_percent": prediction_accuracy_percent(y_true, y_pred),
    }

    return metrics

