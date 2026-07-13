#!/usr/bin/env python3
"""
Signal Generation Engine
Combine multiple indicators to generate trading signals with confidence scores.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


class SignalType(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class SignalComponent:
    """Individual indicator signal."""

    name: str
    signal: SignalType
    weight: float
    value: float
    threshold: str
    reasoning: str


@dataclass
class TradingSignal:
    """Composite trading signal from multiple indicators."""

    symbol: str
    timestamp: pd.Timestamp
    signal: SignalType
    confidence: float  # 0-100
    components: List[SignalComponent] = field(default_factory=list)
    price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": str(self.timestamp),
            "signal": self.signal.value,
            "confidence": round(self.confidence, 1),
            "price": self.price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward": self.risk_reward,
            "components": [
                {"name": c.name, "signal": c.signal.value, "value": round(c.value, 2), "reasoning": c.reasoning}
                for c in self.components
            ],
        }


class SignalGenerator:
    """Generate trading signals from technical indicators."""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.weights = {
            "rsi": self.params.get("rsi_weight", 1.0),
            "macd": self.params.get("macd_weight", 1.0),
            "bollinger": self.params.get("bb_weight", 1.0),
            "trend": self.params.get("trend_weight", 1.0),
            "volume": self.params.get("volume_weight", 0.5),
            "stochastic": self.params.get("stoch_weight", 0.5),
            "adx": self.params.get("adx_weight", 0.5),
        }

    def _signal_to_score(self, signal: SignalType) -> float:
        """Convert signal to numeric score (-2 to +2)."""
        mapping = {
            SignalType.STRONG_BUY: 2,
            SignalType.BUY: 1,
            SignalType.NEUTRAL: 0,
            SignalType.SELL: -1,
            SignalType.STRONG_SELL: -2,
        }
        return mapping[signal]

    def _score_to_signal(self, score: float) -> SignalType:
        """Convert numeric score to signal."""
        if score >= 1.5:
            return SignalType.STRONG_BUY
        elif score >= 0.5:
            return SignalType.BUY
        elif score <= -1.5:
            return SignalType.STRONG_SELL
        elif score <= -0.5:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL

    def analyze_rsi(self, row: pd.Series) -> SignalComponent:
        """Analyze RSI for overbought/oversold conditions."""
        rsi = row["rsi"]
        oversold = self.params.get("rsi_oversold", 30)
        overbought = self.params.get("rsi_overbought", 70)

        if pd.isna(rsi):
            return SignalComponent(
                name="RSI",
                signal=SignalType.NEUTRAL,
                weight=self.weights["rsi"],
                value=50,
                threshold=f"{oversold}/{overbought}",
                reasoning="Insufficient data",
            )

        if rsi < oversold:
            signal = SignalType.STRONG_BUY
            reasoning = f"Oversold at {rsi:.1f} (< {oversold})"
        elif rsi < 40:
            signal = SignalType.BUY
            reasoning = f"Approaching oversold at {rsi:.1f}"
        elif rsi > overbought:
            signal = SignalType.STRONG_SELL
            reasoning = f"Overbought at {rsi:.1f} (> {overbought})"
        elif rsi > 60:
            signal = SignalType.SELL
            reasoning = f"Approaching overbought at {rsi:.1f}"
        else:
            signal = SignalType.NEUTRAL
            reasoning = f"Neutral zone at {rsi:.1f}"

        return SignalComponent(
            name="RSI",
            signal=signal,
            weight=self.weights["rsi"],
            value=rsi,
            threshold=f"{oversold}/{overbought}",
            reasoning=reasoning,
        )

    def analyze_macd(self, row: pd.Series, prev_row: pd.Series = None) -> SignalComponent:
        """Analyze MACD for trend and momentum."""
        macd = row["macd"]
        signal_line = row["macd_signal"]
        histogram = row["macd_hist"]

        if pd.isna(macd) or pd.isna(signal_line):
            return SignalComponent(
                name="MACD",
                signal=SignalType.NEUTRAL,
                weight=self.weights["macd"],
                value=0,
                threshold="crossover",
                reasoning="Insufficient data",
            )

        # Check for crossover
        crossover = False
        if prev_row is not None and not pd.isna(prev_row["macd"]):
            prev_above = prev_row["macd"] > prev_row["macd_signal"]
            curr_above = macd > signal_line
            crossover = prev_above != curr_above

        if macd > signal_line and histogram > 0:
            if crossover:
                signal = SignalType.STRONG_BUY
                reasoning = "Bullish crossover with positive momentum"
            else:
                signal = SignalType.BUY
                reasoning = "MACD above signal, positive momentum"
        elif macd < signal_line and histogram < 0:
            if crossover:
                signal = SignalType.STRONG_SELL
                reasoning = "Bearish crossover with negative momentum"
            else:
                signal = SignalType.SELL
                reasoning = "MACD below signal, negative momentum"
        else:
            signal = SignalType.NEUTRAL
            reasoning = "No clear MACD signal"

        return SignalComponent(
            name="MACD",
            signal=signal,
            weight=self.weights["macd"],
            value=histogram,
            threshold="crossover",
            reasoning=reasoning,
        )

    def analyze_bollinger(self, row: pd.Series) -> SignalComponent:
        """Analyze Bollinger Band position."""
        bb_pct = row["bb_pct"]
        close = row["close"]
        bb_upper = row["bb_upper"]
        bb_lower = row["bb_lower"]

        if pd.isna(bb_pct):
            return SignalComponent(
                name="Bollinger Bands",
                signal=SignalType.NEUTRAL,
                weight=self.weights["bollinger"],
                value=0.5,
                threshold="0.0/1.0",
                reasoning="Insufficient data",
            )

        if bb_pct < 0:
            signal = SignalType.STRONG_BUY
            reasoning = f"Price below lower band ({close:.2f} < {bb_lower:.2f})"
        elif bb_pct < 0.2:
            signal = SignalType.BUY
            reasoning = f"Price near lower band (%B = {bb_pct:.2f})"
        elif bb_pct > 1:
            signal = SignalType.STRONG_SELL
            reasoning = f"Price above upper band ({close:.2f} > {bb_upper:.2f})"
        elif bb_pct > 0.8:
            signal = SignalType.SELL
            reasoning = f"Price near upper band (%B = {bb_pct:.2f})"
        else:
            signal = SignalType.NEUTRAL
            reasoning = f"Price in middle of bands (%B = {bb_pct:.2f})"

        return SignalComponent(
            name="Bollinger Bands",
            signal=signal,
            weight=self.weights["bollinger"],
            value=bb_pct,
            threshold="0.0/1.0",
            reasoning=reasoning,
        )

    def analyze_trend(self, row: pd.Series) -> SignalComponent:
        """Analyze trend using moving averages."""
        close = row["close"]
        sma_20 = row.get("sma_20", np.nan)
        sma_50 = row.get("sma_50", np.nan)
        sma_200 = row.get("sma_200", np.nan)

        if pd.isna(sma_20) or pd.isna(sma_50):
            return SignalComponent(
                name="Trend",
                signal=SignalType.NEUTRAL,
                weight=self.weights["trend"],
                value=0,
                threshold="SMA crossovers",
                reasoning="Insufficient data",
            )

        # Count bullish conditions
        bullish = 0
        bearish = 0

        if close > sma_20:
            bullish += 1
        else:
            bearish += 1

        if close > sma_50:
            bullish += 1
        else:
            bearish += 1

        if not pd.isna(sma_200):
            if close > sma_200:
                bullish += 1
            else:
                bearish += 1

            if sma_50 > sma_200:
                bullish += 1
            else:
                bearish += 1

        score = bullish - bearish

        if score >= 3:
            signal = SignalType.STRONG_BUY
            reasoning = "Strong uptrend: price above all MAs, golden cross"
        elif score >= 1:
            signal = SignalType.BUY
            reasoning = "Uptrend: price above key moving averages"
        elif score <= -3:
            signal = SignalType.STRONG_SELL
            reasoning = "Strong downtrend: price below all MAs, death cross"
        elif score <= -1:
            signal = SignalType.SELL
            reasoning = "Downtrend: price below key moving averages"
        else:
            signal = SignalType.NEUTRAL
            reasoning = "Mixed trend signals"

        return SignalComponent(
            name="Trend",
            signal=signal,
            weight=self.weights["trend"],
            value=score,
            threshold="SMA crossovers",
            reasoning=reasoning,
        )

    def analyze_volume(self, row: pd.Series) -> SignalComponent:
        """Analyze volume for confirmation."""
        volume_ratio = row.get("volume_ratio", np.nan)

        if pd.isna(volume_ratio):
            return SignalComponent(
                name="Volume",
                signal=SignalType.NEUTRAL,
                weight=self.weights["volume"],
                value=1.0,
                threshold="1.5x avg",
                reasoning="Insufficient data",
            )

        change = row.get("change_1d", 0)

        if volume_ratio > 2.0:
            if change > 0:
                signal = SignalType.STRONG_BUY
                reasoning = f"High volume ({volume_ratio:.1f}x) on up move"
            else:
                signal = SignalType.STRONG_SELL
                reasoning = f"High volume ({volume_ratio:.1f}x) on down move"
        elif volume_ratio > 1.5:
            if change > 0:
                signal = SignalType.BUY
                reasoning = f"Above-average volume ({volume_ratio:.1f}x) on up move"
            else:
                signal = SignalType.SELL
                reasoning = f"Above-average volume ({volume_ratio:.1f}x) on down move"
        else:
            signal = SignalType.NEUTRAL
            reasoning = f"Normal volume ({volume_ratio:.1f}x average)"

        return SignalComponent(
            name="Volume",
            signal=signal,
            weight=self.weights["volume"],
            value=volume_ratio,
            threshold="1.5x avg",
            reasoning=reasoning,
        )

    def analyze_stochastic(self, row: pd.Series) -> SignalComponent:
        """Analyze Stochastic oscillator."""
        k = row.get("stoch_k", np.nan)
        d = row.get("stoch_d", np.nan)

        if pd.isna(k) or pd.isna(d):
            return SignalComponent(
                name="Stochastic",
                signal=SignalType.NEUTRAL,
                weight=self.weights["stochastic"],
                value=50,
                threshold="20/80",
                reasoning="Insufficient data",
            )

        if k < 20 and d < 20:
            signal = SignalType.STRONG_BUY
            reasoning = f"Oversold (%K={k:.1f}, %D={d:.1f})"
        elif k < 30:
            signal = SignalType.BUY
            reasoning = f"Approaching oversold (%K={k:.1f})"
        elif k > 80 and d > 80:
            signal = SignalType.STRONG_SELL
            reasoning = f"Overbought (%K={k:.1f}, %D={d:.1f})"
        elif k > 70:
            signal = SignalType.SELL
            reasoning = f"Approaching overbought (%K={k:.1f})"
        else:
            signal = SignalType.NEUTRAL
            reasoning = f"Neutral zone (%K={k:.1f})"

        return SignalComponent(
            name="Stochastic",
            signal=signal,
            weight=self.weights["stochastic"],
            value=k,
            threshold="20/80",
            reasoning=reasoning,
        )

    def analyze_adx(self, row: pd.Series) -> SignalComponent:
        """Analyze ADX for trend strength."""
        adx = row.get("adx", np.nan)
        plus_di = row.get("plus_di", np.nan)
        minus_di = row.get("minus_di", np.nan)

        if pd.isna(adx):
            return SignalComponent(
                name="ADX",
                signal=SignalType.NEUTRAL,
                weight=self.weights["adx"],
                value=20,
                threshold="25 trend threshold",
                reasoning="Insufficient data",
            )

        if adx < 20:
            signal = SignalType.NEUTRAL
            reasoning = f"Weak/no trend (ADX={adx:.1f})"
        elif adx < 25:
            if plus_di > minus_di:
                signal = SignalType.BUY
                reasoning = f"Developing uptrend (ADX={adx:.1f}, +DI>-DI)"
            else:
                signal = SignalType.SELL
                reasoning = f"Developing downtrend (ADX={adx:.1f}, -DI>+DI)"
        else:
            if plus_di > minus_di:
                signal = SignalType.STRONG_BUY if adx > 40 else SignalType.BUY
                reasoning = f"Strong uptrend (ADX={adx:.1f}, +DI={plus_di:.1f})"
            else:
                signal = SignalType.STRONG_SELL if adx > 40 else SignalType.SELL
                reasoning = f"Strong downtrend (ADX={adx:.1f}, -DI={minus_di:.1f})"

        return SignalComponent(
            name="ADX",
            signal=signal,
            weight=self.weights["adx"],
            value=adx,
            threshold="25 trend threshold",
            reasoning=reasoning,
        )

    def calculate_risk_levels(self, price: float, signal: SignalType, atr: float) -> tuple:
        """Calculate stop-loss and take-profit levels."""
        atr_multiplier = self.params.get("atr_multiplier", 2.0)
        risk_reward_target = self.params.get("risk_reward", 2.0)

        if signal in [SignalType.STRONG_BUY, SignalType.BUY]:
            stop_loss = price - (atr * atr_multiplier)
            take_profit = price + (atr * atr_multiplier * risk_reward_target)
        elif signal in [SignalType.STRONG_SELL, SignalType.SELL]:
            stop_loss = price + (atr * atr_multiplier)
            take_profit = price - (atr * atr_multiplier * risk_reward_target)
        else:
            stop_loss = None
            take_profit = None

        risk_reward = risk_reward_target if stop_loss else None

        return stop_loss, take_profit, risk_reward

    def generate_signal(self, df: pd.DataFrame, symbol: str = "Unknown") -> TradingSignal:
        """
        Generate a composite trading signal from all indicators.

        Args:
            df: DataFrame with price data and calculated indicators
            symbol: Trading symbol

        Returns:
            TradingSignal with composite signal and component breakdown
        """
        row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else None

        # Analyze each indicator
        components = [
            self.analyze_rsi(row),
            self.analyze_macd(row, prev_row),
            self.analyze_bollinger(row),
            self.analyze_trend(row),
            self.analyze_volume(row),
            self.analyze_stochastic(row),
            self.analyze_adx(row),
        ]

        # Calculate weighted score
        total_weight = sum(c.weight for c in components)
        weighted_score = sum(self._signal_to_score(c.signal) * c.weight for c in components) / total_weight

        # Convert to composite signal
        composite_signal = self._score_to_signal(weighted_score)

        # Calculate confidence (0-100)
        # Higher when components agree, lower when mixed
        scores = [self._signal_to_score(c.signal) for c in components]
        agreement = 1 - (np.std(scores) / 2)  # 0 to 1
        strength = abs(weighted_score) / 2  # 0 to 1
        confidence = min(100, (agreement * 0.5 + strength * 0.5) * 100)

        # Calculate risk levels
        atr = row.get("atr", 0)
        stop_loss, take_profit, risk_reward = self.calculate_risk_levels(row["close"], composite_signal, atr)

        return TradingSignal(
            symbol=symbol,
            timestamp=df.index[-1],
            signal=composite_signal,
            confidence=confidence,
            components=components,
            price=row["close"],
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=risk_reward,
        )


def format_signal(signal: TradingSignal) -> str:
    """Format trading signal for display."""
    lines = []

    # Signal header with emoji
    emoji = {
        SignalType.STRONG_BUY: "🟢🟢",
        SignalType.BUY: "🟢",
        SignalType.NEUTRAL: "⚪",
        SignalType.SELL: "🔴",
        SignalType.STRONG_SELL: "🔴🔴",
    }

    lines.append("=" * 70)
    lines.append(f"  {emoji[signal.signal]} {signal.symbol} - {signal.signal.value}")
    lines.append(f"  Confidence: {signal.confidence:.1f}% | Price: ${signal.price:,.2f}")
    lines.append("=" * 70)

    # Risk levels
    if signal.stop_loss:
        lines.append("\n  Risk Management:")
        lines.append(f"    Stop Loss:   ${signal.stop_loss:,.2f}")
        lines.append(f"    Take Profit: ${signal.take_profit:,.2f}")
        lines.append(f"    Risk/Reward: 1:{signal.risk_reward:.1f}")

    # Component breakdown
    lines.append("\n  Signal Components:")
    lines.append("-" * 70)

    for comp in signal.components:
        indicator_emoji = emoji[comp.signal]
        lines.append(f"    {indicator_emoji} {comp.name:15} | {comp.signal.value:12} | {comp.reasoning}")

    lines.append("-" * 70)
    lines.append(f"  Generated: {signal.timestamp}")
    lines.append("")

    return "\n".join(lines)
