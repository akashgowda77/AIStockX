"""Prediction pipeline (data preparation only).

Phase 8 goal:
- Create a reusable orchestration layer that prepares model-ready datasets.

Workflow (no ML here):
1) Download stock history using stock_service
2) Clean using data_pipeline
3) Generate engineered features
4) Generate technical indicators
5) Validate final dataset
6) Return processed dataframe + metadata

Public functions:
- prepare_prediction_data(symbol, period="5y", interval="1d")
- get_latest_prediction_features(symbol)

No training, no prediction, no evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from ..services.data_pipeline import clean_stock_data, prepare_features
from ..services.data_pipeline import validate_dataset as validate_basic_dataset
from .indicator_service import generate_all_indicators
from .stock_service import get_historical_data, validate_symbol


TARGET_COLUMN = "target_close_next"


# Keep this in sync with data_pipeline.prepare_ml_dataset
FEATURE_COLUMNS = [
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

    "sma_20",
    "ema_20",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "bb_middle",
    "bb_upper",
    "bb_lower",
    "atr_14",
    "obv",
    "stoch_k_14",
    "stoch_d_14",
]


def _add_target_next_close(df: pd.DataFrame) -> pd.DataFrame:
    """Add target_close_next to the dataframe.

    Input:
        df: dataframe with 'close'
    Output:
        df copy with target column added
    """

    data = df.copy()
    data[TARGET_COLUMN] = data["close"].shift(-1)
    return data


def prepare_prediction_data(symbol: str, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
    """Prepare a model-ready dataset for forecasting.

    Input:
        symbol: stock symbol
        period: yfinance period (e.g. '1y', '5y')
        interval: yfinance interval (e.g. '1d')

    Output:
        dict with:
        - dataframe: processed dataframe with target + engineered features
        - feature_columns: list of feature column names
        - target_column: "target_close_next"
        - metadata: rows, symbol, date_range

    Notes:
        - We do not perform ML training/prediction.
        - Dataset is chronological.
    """

    symbol_normalized = validate_symbol(symbol)

    rows = get_historical_data(symbol=symbol_normalized, period=period, interval=interval)
    raw_df = pd.DataFrame(rows)

    cleaned_df = clean_stock_data(raw_df)

    # Basic validation before feature engineering (row/columns/missing)
    is_valid, messages = validate_basic_dataset(cleaned_df)
    if not is_valid:
        raise ValueError("Invalid dataset: " + "; ".join(messages))

    # Engineered features from data pipeline
    features_df = prepare_features(cleaned_df)

    # Add indicators
    enriched_df = generate_all_indicators(features_df)

    if enriched_df.empty:
        raise ValueError(
            "Indicator generation returned an empty dataset."
        )
    
    # Add target
    final_df = _add_target_next_close(enriched_df)

    # Drop rows that can't be used for training due to missing target
    final_df = final_df.dropna().reset_index(drop=True)

    if final_df.empty:
        raise ValueError(
            "No training data remains after preprocessing."
        )
    
    # Validate final dataset (lightweight)
    # We only validate required columns for Phase 8, since indicators create extra columns.
    is_valid_final, messages_final = validate_basic_dataset(final_df)
    if not is_valid_final:
        raise ValueError("Final dataset invalid: " + "; ".join(messages_final))

    feature_columns = FEATURE_COLUMNS

    date_min = str(final_df["date"].min()) if "date" in final_df.columns else None
    date_max = str(final_df["date"].max()) if "date" in final_df.columns else None

    return {
        "dataframe": final_df,
        "feature_columns": feature_columns,
        "target_column": TARGET_COLUMN,
        "metadata": {
            "rows": len(final_df),
            "feature_count": len(feature_columns),
            "target_column": TARGET_COLUMN,
            "symbol": symbol_normalized,
            "date_range": [date_min, date_max],
        },
    }


def get_latest_prediction_features(symbol: str) -> Dict[str, Any]:
    """Get the latest processed feature row for a symbol.

    Input:
        symbol
    Output:
        dict containing the latest row as a feature mapping.

    Notes:
        - Uses default period/interval for latest features.
        - Does not do ML.
    """

    payload = prepare_prediction_data(symbol=symbol, period="1y", interval="1d")
    print("Payload metadata:", payload["metadata"])
    print("Training rows:", payload["metadata"]["rows"])
    
    df = payload["dataframe"]
    feature_columns = [
        col
        for col in payload["feature_columns"]
        if col in df.columns
    ]

    if df.empty:
        raise ValueError(f"No data available for {symbol}")

    latest = df.iloc[-1]
    latest_features: Dict[str, Any] = {}
    for col in feature_columns:
        val = latest.get(col)
        if pd.isna(val):
            latest_features[col] = None
        else:
            if hasattr(val, "item"):
                latest_features[col] = val.item()
            else:
                latest_features[col] = float(val) if isinstance(val, (int, float)) else val

    # Include also latest date/close for convenience
    return {
        "symbol": payload["metadata"]["symbol"],
        "date": str(latest.get("date")) if "date" in latest else None,
        "latest_close": float(latest.get("close")) if latest.get("close") is not None else None,
        "features": latest_features,
    }

