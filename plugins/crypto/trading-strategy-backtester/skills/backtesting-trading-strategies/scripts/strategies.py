#!/usr/bin/env python3
"""
Trading Strategy Definitions
Each strategy implements generate_signals() returning entry/exit signals.
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Signal:
    """Trading signal with entry/exit information."""
    entry: bool = False
    exit: bool = False
    direction: str = "long"  # "long" or "short"
    strength: float = 1.0    # Signal strength 0-1


class Strategy(ABC):
    """Base class for all trading strategies."""
    
    name: str = "base"
    lookback: int = 1
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        """Generate trading signals from price data."""
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and set default parameters."""
        return params


class SMAcrossover(Strategy):
    """Simple Moving Average Crossover Strategy.
    
    Buy when fast MA crosses above slow MA (golden cross).
    Sell when fast MA crosses below slow MA (death cross).
    """
    
    name = "sma_crossover"
    lookback = 200
    
    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        params = self.validate_params(params)
        fast = params.get("fast_period", 20)
        slow = params.get("slow_period", 50)

        if len(data) < slow + 1:
            return Signal()

        close = data["close"]
        fast_ma = close.rolling(window=fast).mean()
        slow_ma = close.rolling(window=slow).mean()

        # Current and previous values
        curr_fast, prev_fast = fast_ma.iloc[-1], fast_ma.iloc[-2]
        curr_slow, prev_slow = slow_ma.iloc[-1], slow_ma.iloc[-2]

        # Golden cross: fast crosses above slow (long only)
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return Signal(entry=True, direction="long")

        # Death cross: fast crosses below slow (exit long)
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return Signal(exit=True)

        return Signal()


class EMAcrossover(Strategy):
    """Exponential Moving Average Crossover Strategy."""
    
    name = "ema_crossover"
    lookback = 200
    
    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        fast = params.get("fast_period", 12)
        slow = params.get("slow_period", 26)
        
        if len(data) < slow + 1:
            return Signal()
        
        close = data["close"]
        fast_ema = close.ewm(span=fast, adjust=False).mean()
        slow_ema = close.ewm(span=slow, adjust=False).mean()
        
        curr_fast, prev_fast = fast_ema.iloc[-1], fast_ema.iloc[-2]
        curr_slow, prev_slow = slow_ema.iloc[-1], slow_ema.iloc[-2]
        
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return Signal(entry=True, direction="long")
        
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return Signal(exit=True)
        
        return Signal()


class RSIreversal(Strategy):
    """RSI Overbought/Oversold Reversal Strategy.

    Long when RSI crosses above oversold. Short when RSI crosses below overbought.
    """

    name = "rsi_reversal"
    lookback = 14

    def _calculate_rsi(self, close: pd.Series, period: int) -> pd.Series:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        period = params.get("period", 14)
        overbought = params.get("overbought", 70)
        oversold = params.get("oversold", 30)

        if len(data) < period + 1:
            return Signal()

        rsi = self._calculate_rsi(data["close"], period)
        curr_rsi, prev_rsi = rsi.iloc[-1], rsi.iloc[-2]

        # Oversold reversal: enter long (also exits any short)
        if prev_rsi <= oversold and curr_rsi > oversold:
            return Signal(entry=True, exit=True, direction="long", strength=min(1.0, (oversold - prev_rsi) / 10))

        # Overbought reversal: enter short (also exits any long)
        if prev_rsi >= overbought and curr_rsi < overbought:
            return Signal(entry=True, exit=True, direction="short", strength=min(1.0, (prev_rsi - overbought) / 10))

        return Signal()


class MACD(Strategy):
    """MACD Signal Line Crossover Strategy (long and short)."""

    name = "macd"
    lookback = 35

    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        fast = params.get("fast", 12)
        slow = params.get("slow", 26)
        signal_period = params.get("signal", 9)

        if len(data) < slow + signal_period:
            return Signal()

        close = data["close"]
        fast_ema = close.ewm(span=fast, adjust=False).mean()
        slow_ema = close.ewm(span=slow, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        curr_macd, prev_macd = macd_line.iloc[-1], macd_line.iloc[-2]
        curr_signal, prev_signal = signal_line.iloc[-1], signal_line.iloc[-2]

        # Bullish crossover: enter long, exit short
        if prev_macd <= prev_signal and curr_macd > curr_signal:
            return Signal(entry=True, exit=True, direction="long")

        # Bearish crossover: enter short, exit long
        if prev_macd >= prev_signal and curr_macd < curr_signal:
            return Signal(entry=True, exit=True, direction="short")

        return Signal()


class BollingerBands(Strategy):
    """Bollinger Bands Mean Reversion Strategy (long and short).

    Long when price touches lower band. Short when price crosses upper band.
    Exit at middle band.
    """

    name = "bollinger_bands"
    lookback = 20

    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        period = params.get("period", 20)
        std_dev = params.get("std_dev", 2.0)

        if len(data) < period:
            return Signal()

        close = data["close"]
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        curr_close = close.iloc[-1]
        prev_close = close.iloc[-2]

        # Price crosses below lower band: enter long, exit short
        if prev_close >= lower_band.iloc[-2] and curr_close < lower_band.iloc[-1]:
            return Signal(entry=True, exit=True, direction="long")

        # Price crosses above upper band: enter short, exit long
        if prev_close <= upper_band.iloc[-2] and curr_close > upper_band.iloc[-1]:
            return Signal(entry=True, exit=True, direction="short")

        # Price crosses middle band: exit any position
        curr_mid = sma.iloc[-1]
        prev_mid = sma.iloc[-2]
        if (prev_close < prev_mid and curr_close >= curr_mid) or \
           (prev_close > prev_mid and curr_close <= curr_mid):
            return Signal(exit=True)

        return Signal()


class Breakout(Strategy):
    """Price Breakout Strategy.
    
    Buy when price breaks above recent high.
    Sell when price breaks below recent low.
    """
    
    name = "breakout"
    lookback = 20
    
    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        lookback = params.get("lookback", 20)
        threshold = params.get("threshold", 0.0)  # % above/below
        
        if len(data) < lookback + 1:
            return Signal()
        
        high = data["high"].iloc[-lookback-1:-1]
        low = data["low"].iloc[-lookback-1:-1]
        curr_close = data["close"].iloc[-1]
        
        resistance = high.max() * (1 + threshold / 100)
        support = low.min() * (1 - threshold / 100)
        
        # Breakout above resistance
        if curr_close > resistance:
            return Signal(entry=True, direction="long")
        
        # Breakdown below support
        if curr_close < support:
            return Signal(exit=True)
        
        return Signal()


class MeanReversion(Strategy):
    """Mean Reversion Strategy (long and short).

    Long when price deviates below mean. Short when price deviates above mean.
    Exit when z-score crosses zero.
    """

    name = "mean_reversion"
    lookback = 20

    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        period = params.get("period", 20)
        z_threshold = params.get("z_threshold", 2.0)

        if len(data) < period:
            return Signal()

        close = data["close"]
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        if std.iloc[-1] == 0 or std.iloc[-2] == 0:
            return Signal()

        z_score = (close.iloc[-1] - sma.iloc[-1]) / std.iloc[-1]
        prev_z_score = (close.iloc[-2] - sma.iloc[-2]) / std.iloc[-2]

        # Price significantly below mean: enter long, exit short
        if z_score < -z_threshold and prev_z_score >= -z_threshold:
            return Signal(entry=True, exit=True, direction="long", strength=min(1.0, abs(z_score) / 3))

        # Price significantly above mean: enter short, exit long
        if z_score > z_threshold and prev_z_score <= z_threshold:
            return Signal(entry=True, exit=True, direction="short", strength=min(1.0, abs(z_score) / 3))

        # Price reverts to mean: exit any position
        if (prev_z_score < 0 and z_score >= 0) or (prev_z_score > 0 and z_score <= 0):
            return Signal(exit=True)

        return Signal()


class Momentum(Strategy):
    """Rate of Change Momentum Strategy."""
    
    name = "momentum"
    lookback = 14
    
    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        period = params.get("period", 14)
        threshold = params.get("threshold", 5.0)  # % change threshold
        
        if len(data) < period + 1:
            return Signal()
        
        close = data["close"]
        roc = ((close.iloc[-1] - close.iloc[-period]) / close.iloc[-period]) * 100
        prev_roc = ((close.iloc[-2] - close.iloc[-period-1]) / close.iloc[-period-1]) * 100
        
        # Momentum turns positive and exceeds threshold
        if prev_roc <= threshold and roc > threshold:
            return Signal(entry=True, direction="long")
        
        # Momentum turns negative
        if prev_roc >= 0 and roc < 0:
            return Signal(exit=True)
        
        return Signal()


# Strategy registry
STRATEGIES = {
    "sma_crossover": SMAcrossover(),
    "ema_crossover": EMAcrossover(),
    "rsi_reversal": RSIreversal(),
    "macd": MACD(),
    "bollinger_bands": BollingerBands(),
    "breakout": Breakout(),
    "mean_reversion": MeanReversion(),
    "momentum": Momentum(),
}


def get_strategy(name: str) -> Strategy:
    """Get strategy by name."""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]


def list_strategies() -> Dict[str, str]:
    """List all available strategies with descriptions."""
    return {name: strategy.__doc__.split('\n')[0] for name, strategy in STRATEGIES.items()}
