"""Financial data processing pipeline.

This phase prepares raw market data for later ML modules.

Implemented functions (beginner friendly):
- clean_stock_data(df): cleaning + sorting + missing handling
- validate_dataset(df): checks required columns & basic quality
- prepare_features(df): feature engineering
- prepare_ml_dataset(df): returns (X, y)

Important:
- No indicators yet
- No ML training/prediction yet

Data expectations:
- Input df typically comes from yfinance.
- We assume OHLCV-like columns are present.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from ..utils.data_utils import ensure_datetime_column, standardize_columns


REQUIRED_COLUMNS = {
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
}

NUMERIC_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
]

ROLLING_WINDOW = 14

MIN_ROWS = 30

TARGET_COLUMN = "target_close_next"

def validate_dataset(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate that a dataframe is suitable for feature engineering.

    Input:
        df: pandas DataFrame
    Output:
        (is_valid, messages)

    Validation rules:
    - Must be a DataFrame
    - Must have enough rows (> 30)
    - Must contain required columns
    - Must not be entirely missing
    """

    messages: List[str] = []

    if df is None or not isinstance(df, pd.DataFrame):
        return False, ["df must be a pandas DataFrame"]

    if len(df) < MIN_ROWS:
        messages.append("Not enough rows. Need at least 30 rows.")

    # Standardize column names (defensive)
    df_std = standardize_columns(df.copy())

    missing_cols = sorted(list(REQUIRED_COLUMNS - set(df_std.columns)))
    if missing_cols:
        messages.append(f"Missing required columns: {missing_cols}")

    # Quick missing-value check
    missing_ratio = df_std[list(REQUIRED_COLUMNS)].isna().mean().mean() if set(REQUIRED_COLUMNS).issubset(df_std.columns) else 1.0
    if missing_ratio > 0.2:
        messages.append("Too many missing values in required columns.")

    is_valid = len(messages) == 0
    return is_valid, messages


def clean_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw stock data.

    Responsibilities:
    - Remove duplicate rows
    - Handle missing values
    - Convert date column to datetime
    - Sort chronologically
    - Reset index

    Input:
        df: raw DataFrame
    Output:
        cleaned DataFrame with standardized columns
    """

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame")

    df_std = standardize_columns(df.copy())

    # Ensure date is datetime
    df_std = ensure_datetime_column(df_std, date_col="date")

    # Remove duplicates
    df_std = df_std.drop_duplicates()

    # Sort by date
    df_std = df_std.sort_values("date")

    # Handle missing values:
    # - For numeric columns: forward fill, then back fill
    # - Finally drop rows that still have missing required values
   
    for col in NUMERIC_COLUMNS:
        if col in df_std.columns:
            df_std[col] = df_std[col].ffill().bfill()

    df_std = df_std.dropna(
        subset=[c for c in NUMERIC_COLUMNS if c in df_std.columns]
    )
    # Reset index after cleaning
    df_std = df_std.reset_index(drop=True)

    return df_std


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create ML-ready features from cleaned OHLCV data.

    Input:
        df: cleaned stock dataframe (must include required columns)
    Output:
        dataframe with engineered features + original columns
    """

    # Work on a copy
    data = df.copy()

    # Daily return and log return based on close
    data["daily_return"] = data["close"].pct_change()
    data["log_return"] = np.log(data["close"].replace(0, np.nan)).diff()

    # Price change
    data["price_change"] = data["close"].diff()

    # High-Low difference
    data["high_low_diff"] = data["high"] - data["low"]

    # Open-Close difference
    data["open_close_diff"] = data["close"] - data["open"]

    # Volume change percentage
    data["volume_change_pct"] = data["volume"].pct_change()

    # Rolling statistics (simple defaults for beginner readability)
    window = ROLLING_WINDOW
    data["rolling_mean"] = data["close"].rolling(window=window).mean()
    data["rolling_std"] = data["close"].rolling(window=window).std()

    # Momentum: close - close(t-14)
    data["momentum"] = data["close"] - data["close"].shift(window)

    # Volatility: rolling std of returns
    data["volatility"] = data["daily_return"].rolling(window=window).std()

    # Drop rows where features could not be computed
    feature_columns = [
        "daily_return",
        "log_return",
        "price_change",
        "high_low_diff",
        "open_close_diff",
        "volume_change_pct",
        "rolling_mean",
        "rolling_std",
        "momentum",
        "volatility",
    ]

    data = data.dropna(
        subset=feature_columns
    ).reset_index(drop=True)

    if data.empty:
        raise ValueError(
            "Feature engineering produced an empty dataset."
        )
    return data


def prepare_ml_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepare X (features) and y (target) for ML models.

    Target choice (simple):
    - Predict next day's close price.

    Input:
        df: raw or cleaned dataframe
    Output:
        (X, y)
    """

    cleaned = clean_stock_data(df)
    features_df = prepare_features(cleaned)

    # Target: next day's close
    features_df[TARGET_COLUMN] = features_df["close"].shift(-1)

    # Remove last row because target is NaN
    features_df = features_df.dropna().reset_index(drop=True)

    feature_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "daily_return",
        "log_return",
        "price_change",
        "high_low_diff",
        "open_close_diff",
        "volume_change_pct",
        "rolling_mean",
        "rolling_std",
        "momentum",
        "volatility",
    ]

    X = features_df[feature_columns]
    y = features_df[TARGET_COLUMN]

    return X, y

