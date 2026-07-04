"""Dataframe helper utilities.

Kept separate for readability.

These helpers are used by the data pipeline and later by indicator/ML modules.
"""

from __future__ import annotations

from typing import Dict

import pandas as pd


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to the expected lowercase schema.

    Input:
        df: DataFrame with possible columns like Date/Open/Close
    Output:
        DataFrame with columns: date, open, high, low, close, volume

    Note:
        This function is intentionally simple and beginner-friendly.
    """

    rename_map: Dict[str, str] = {}

    for col in df.columns:
        col_lower = str(col).strip().lower()
        if col_lower in {"date", "datetime", "time"}:
            rename_map[col] = "date"
        elif col_lower == "open":
            rename_map[col] = "open"
        elif col_lower == "high":
            rename_map[col] = "high"
        elif col_lower == "low":
            rename_map[col] = "low"
        elif col_lower == "close":
            rename_map[col] = "close"
        elif col_lower == "volume":
            rename_map[col] = "volume"

    return df.rename(columns=rename_map)


def ensure_datetime_column(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Convert a date column into pandas datetime.

    Input:
        df: DataFrame
        date_col: name of date column
    Output:
        DataFrame with converted datetime column

    Raises:
        ValueError if date column missing or conversion fails.
    """

    if date_col not in df.columns:
        raise ValueError(f"Missing date column: {date_col}")

    # Convert using pandas
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    if df[date_col].isna().all():
        raise ValueError("All date values became NaT after conversion")

    return df

