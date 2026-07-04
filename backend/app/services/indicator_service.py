"""Technical indicators service.

Goal (Phase 7):
- Calculate a set of common technical indicators using only pandas + NumPy.
- Provide `generate_all_indicators(df)` which enriches a cleaned OHLCV dataframe.

Rules:
- No TA-Lib
- Do not modify original dataframe in place.

Assumptions:
- Input dataframe is expected to have at least:
  date, open, high, low, close, volume
- Output dataframe will append new indicator columns.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

SMA_WINDOW = 20
EMA_WINDOW = 20
RSI_WINDOW = 14
BB_WINDOW = 20
ATR_WINDOW = 14
STOCH_WINDOW = 14

def simple_moving_average(df: pd.DataFrame, window: int) -> pd.Series:
    """Simple Moving Average (SMA).

    Formula:
        SMA(t) = mean(close over last `window` periods)

    Input:
        df: dataframe with 'close'
        window: lookback window
    Output:
        pandas Series of SMA values
    Interpretation:
        - Price above SMA often considered bullish (trend up)
    """

    return df["close"].rolling(window=window).mean()


def exponential_moving_average(df: pd.DataFrame, window: int) -> pd.Series:
    """Exponential Moving Average (EMA).

    Formula (pandas ewm):
        EMA uses exponentially decaying weights

    Input:
        df: dataframe with 'close'
        window: lookback window
    Output:
        pandas Series of EMA values
    Interpretation:
        - Faster than SMA, responds quicker to price changes
    """

    return df["close"].ewm(span=window, adjust=False).mean()


def relative_strength_index(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Relative Strength Index (RSI).

    Formula (Wilder's RSI):
        RSI = 100 - (100 / (1 + RS))
        RS = avg_gain / avg_loss

    Input:
        df: dataframe with 'close'
        window: lookback window (default 14)
    Output:
        RSI series (0-100)
    Interpretation:
        - RSI > 70: often considered overbought (bearish / pullback risk)
        - RSI < 30: often considered oversold (bullish / rebound risk)
    """

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def moving_average_convergence_divergence(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """MACD (Moving Average Convergence Divergence).

    Default parameters:
    - EMA12 and EMA26

    Formula:
        MACD = EMA12 - EMA26
        Signal = EMA(MACD, 9)
        Histogram = MACD - Signal

    Input:
        df: dataframe with 'close'
    Output:
        dict of series: macd, signal, histogram
    Interpretation:
        - macd above signal => bullish momentum
    """

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return {"macd": macd, "macd_signal": signal, "macd_hist": histogram}


def bollinger_bands(df: pd.DataFrame, window: int = 20) -> Dict[str, pd.Series]:
    """Bollinger Bands.

    Formula:
        middle = SMA(window)
        std = standard deviation over window
        upper = middle + 2*std
        lower = middle - 2*std

    Input:
        df: dataframe with 'close'
        window: lookback window
    Output:
        dict of series: bb_middle, bb_upper, bb_lower
    Interpretation:
        - Price near upper band: bullish momentum (overbought risk)
        - Price near lower band: bearish / oversold rebound risk
    """

    middle = df["close"].rolling(window=window).mean()
    std = df["close"].rolling(window=window).std()
    upper = middle + 2 * std
    lower = middle - 2 * std
    return {"bb_middle": middle, "bb_upper": upper, "bb_lower": lower}


def average_true_range(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range (ATR).

    Formula:
        TR = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        ATR = rolling mean of TR

    Input:
        df: dataframe with 'high','low','close'
        window: lookback window
    Output:
        ATR series
    Interpretation:
        - ATR measures volatility; higher ATR => larger price swings
    """

    prev_close = df["close"].shift(1)
    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - prev_close).abs()
    low_prev_close = (df["low"] - prev_close).abs()

    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    return atr


def on_balance_volume(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume (OBV).

    Formula:
        OBV starts at 0.
        If close increases: OBV = OBV_prev + volume
        If close decreases: OBV = OBV_prev - volume
        If unchanged: OBV = OBV_prev

    Input:
        df: dataframe with 'close','volume'
    Output:
        OBV series
    Interpretation:
        - Rising OBV with price => bullish confirmation
    """

    close_diff = df["close"].diff()
    direction = np.where(close_diff > 0, 1, np.where(close_diff < 0, -1, 0))
    obv = (direction * df["volume"]).fillna(0).cumsum()
    return obv


def stochastic_oscillator(df: pd.DataFrame, window: int = 14) -> Dict[str, pd.Series]:
    """Stochastic Oscillator.

    Formula:
        %K = 100 * (close - lowest_low) / (highest_high - lowest_low)
        %D = SMA(%K, 3)

    Input:
        df: dataframe with 'high','low','close'
        window: lookback for high/low range
    Output:
        dict: stoch_k, stoch_d
    Interpretation:
        - %K/%D > 80: overbought
        - %K/%D < 20: oversold
    """

    lowest_low = df["low"].rolling(window=window).min()
    highest_high = df["high"].rolling(window=window).max()

    denom = (highest_high - lowest_low).replace(0, np.nan)
    stoch_k = 100 * (df["close"] - lowest_low) / denom
    stoch_d = stoch_k.rolling(window=3).mean()
    return {"stoch_k": stoch_k, "stoch_d": stoch_d}


def generate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate and append all supported indicators.

    Input:
        df: cleaned OHLCV dataframe
    Output:
        new enriched dataframe (original df is not modified)

    Indicator columns produced:
    - sma_20
    - ema_20
    - rsi_14
    - macd, macd_signal, macd_hist
    - bb_middle, bb_upper, bb_lower
    - atr_14
    - obv
    - stoch_k_14, stoch_d_14

    Notes:
    - Default windows chosen for common usage.
    """
    required_columns = {
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    data = df.copy()

    # Moving averages
    data["sma_20"] = simple_moving_average(data, window=SMA_WINDOW)
    data["ema_20"] = exponential_moving_average(data, window=EMA_WINDOW)

    # RSI
    data["rsi_14"] = relative_strength_index(data, window=RSI_WINDOW)

    # MACD
    macd_dict = moving_average_convergence_divergence(data)
    data["macd"] = macd_dict["macd"]
    data["macd_signal"] = macd_dict["macd_signal"]
    data["macd_hist"] = macd_dict["macd_hist"]

    # Bollinger Bands
    bb_dict = bollinger_bands(data, window=20)
    data["bb_middle"] = bb_dict["bb_middle"]
    data["bb_upper"] = bb_dict["bb_upper"]
    data["bb_lower"] = bb_dict["bb_lower"]

    # ATR
    data["atr_14"] = average_true_range(data, window=ATR_WINDOW)

    # OBV
    data["obv"] = on_balance_volume(data)

    # Stochastic
    stoch_dict = stochastic_oscillator(data, window=STOCH_WINDOW)
    data["stoch_k_" + str(STOCH_WINDOW)] = stoch_dict["stoch_k"]
    data["stoch_d_" + str(STOCH_WINDOW)] = stoch_dict["stoch_d"]

    if data.empty:
        raise ValueError(
            "Indicator generation produced an empty dataset."
        )

    return data

