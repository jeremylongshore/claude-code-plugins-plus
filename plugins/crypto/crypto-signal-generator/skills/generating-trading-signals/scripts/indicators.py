#!/usr/bin/env python3
"""
Technical Indicators Library
Calculate RSI, MACD, Bollinger Bands, and other technical indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(
    data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Returns:
        macd_line: MACD line (fast EMA - slow EMA)
        signal_line: Signal line (EMA of MACD)
        histogram: MACD histogram (MACD - Signal)
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)

    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    data: pd.Series, period: int = 20, std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Returns:
        upper: Upper band
        middle: Middle band (SMA)
        lower: Lower band
    """
    middle = calculate_sma(data, period)
    std = data.rolling(window=period).std()

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return upper, middle, lower


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high_low = high - low
    high_close = abs(high - close.shift())
    low_close = abs(low - close.shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr


def calculate_stochastic(
    high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.

    Returns:
        k: %K line
        d: %D line (SMA of %K)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()

    return k, d


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume."""
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate Volume Weighted Average Price (intraday)."""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap


def calculate_adx(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Average Directional Index.

    Returns:
        adx: ADX line
        plus_di: +DI line
        minus_di: -DI line
    """
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    # Calculate directional movement
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    # Calculate DI
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    return adx, plus_di, minus_di


def calculate_all_indicators(df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Calculate all indicators for a price DataFrame.

    Args:
        df: DataFrame with columns: open, high, low, close, volume
        params: Optional custom parameters for indicators

    Returns:
        DataFrame with all indicators added
    """
    params = params or {}
    result = df.copy()

    # Price data
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # Moving Averages
    result["sma_20"] = calculate_sma(close, 20)
    result["sma_50"] = calculate_sma(close, 50)
    result["sma_200"] = calculate_sma(close, 200)
    result["ema_12"] = calculate_ema(close, 12)
    result["ema_26"] = calculate_ema(close, 26)

    # RSI
    rsi_period = params.get("rsi_period", 14)
    result["rsi"] = calculate_rsi(close, rsi_period)

    # MACD
    macd_fast = params.get("macd_fast", 12)
    macd_slow = params.get("macd_slow", 26)
    macd_signal = params.get("macd_signal", 9)
    result["macd"], result["macd_signal"], result["macd_hist"] = calculate_macd(
        close, macd_fast, macd_slow, macd_signal
    )

    # Bollinger Bands
    bb_period = params.get("bb_period", 20)
    bb_std = params.get("bb_std", 2.0)
    result["bb_upper"], result["bb_middle"], result["bb_lower"] = calculate_bollinger_bands(close, bb_period, bb_std)
    result["bb_width"] = (result["bb_upper"] - result["bb_lower"]) / result["bb_middle"]
    result["bb_pct"] = (close - result["bb_lower"]) / (result["bb_upper"] - result["bb_lower"])

    # ATR
    atr_period = params.get("atr_period", 14)
    result["atr"] = calculate_atr(high, low, close, atr_period)
    result["atr_pct"] = result["atr"] / close * 100

    # Stochastic
    stoch_k = params.get("stoch_k", 14)
    stoch_d = params.get("stoch_d", 3)
    result["stoch_k"], result["stoch_d"] = calculate_stochastic(high, low, close, stoch_k, stoch_d)

    # Volume Indicators
    result["obv"] = calculate_obv(close, volume)
    result["volume_sma"] = calculate_sma(volume, 20)
    result["volume_ratio"] = volume / result["volume_sma"]

    # ADX
    adx_period = params.get("adx_period", 14)
    result["adx"], result["plus_di"], result["minus_di"] = calculate_adx(high, low, close, adx_period)

    # Price changes
    result["change_1d"] = close.pct_change() * 100
    result["change_7d"] = close.pct_change(7) * 100
    result["change_30d"] = close.pct_change(30) * 100

    return result


if __name__ == "__main__":
    # Quick test
    import yfinance as yf

    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(period="1y", interval="1d")
    df.columns = [c.lower() for c in df.columns]

    result = calculate_all_indicators(df)
    print(f"Calculated {len([c for c in result.columns if c not in df.columns])} indicators")
    print("\nLatest values:")
    print(f"  RSI: {result['rsi'].iloc[-1]:.2f}")
    print(f"  MACD: {result['macd'].iloc[-1]:.2f}")
    print(f"  BB %B: {result['bb_pct'].iloc[-1]:.2f}")
    print(f"  ADX: {result['adx'].iloc[-1]:.2f}")
