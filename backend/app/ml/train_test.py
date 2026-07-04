"""Dataset splitting utilities.

Important requirement:
- Do NOT shuffle market data.
- Use chronological splits.

We provide:
- split_dataset(): simple train/test chronological split
- time_series_split(): rolling/fold splits for time-series

These are reusable by all future models.
"""

from __future__ import annotations

from typing import Generator, Tuple, Any

import numpy as np
import pandas as pd


def split_dataset(X, y, test_ratio: float = 0.2) -> Tuple[Any, Any, Any, Any]:
    """Chronologically split dataset into train and test.

    Input:
        X: features (numpy array or pandas dataframe)
        y: targets (numpy array or pandas series)
        test_ratio: portion of data to use for test (e.g. 0.2)
    Output:
        X_train, X_test, y_train, y_test
    """

    if test_ratio <= 0 or test_ratio >= 1:
        raise ValueError("test_ratio must be between 0 and 1")

    n = len(y)
    if n < 10:
        raise ValueError(
            "Dataset must contain at least 10 samples."
        )
    test_size = int(n * test_ratio)
    train_size = n - test_size

    X_train = X[:train_size]
    X_test = X[train_size:]
    y_train = y[:train_size]
    y_test = y[train_size:]

    return X_train, X_test, y_train, y_test


def time_series_split(X, y, n_splits: int = 5) -> Generator[Tuple[Any, Any, Any, Any], None, None]:
    """Generate chronological time-series splits.

    Input:
        X: features
        y: targets
        n_splits: number of folds
    Output:
        yields (X_train, X_val, y_train, y_val)

    Strategy:
    - Expanding window training
    - Validation window moves forward
    """

    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")

    n = len(y)
    fold_size = n // n_splits
    if fold_size == 0:
        raise ValueError("Not enough data for the requested number of splits")

    for i in range(1, n_splits):
        val_start = i * fold_size
        val_end = (i + 1) * fold_size if i < n_splits - 1 else n

        X_train = X[:val_start]
        y_train = y[:val_start]
        if len(y_train) == 0:
            continue
        X_val = X[val_start:val_end]
        y_val = y[val_start:val_end]

        if len(y_val) == 0:
            continue

        yield X_train, X_val, y_train, y_val

