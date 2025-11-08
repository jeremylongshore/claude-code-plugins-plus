# Crypto Signal Generator

Generate trading signals from technical indicators, chart patterns, and multi-timeframe analysis for cryptocurrency markets.

## Installation

```bash
/plugin install crypto-signal-generator@claude-code-plugins-plus
```

## Usage

### Generate Signal Command

```bash
/generate-signal
```

Or use the shortcut:
```bash
/signal
```

### Example Queries

```bash
# Basic signal generation
/signal Generate signal for BTC/USDT

# Specific timeframe
/signal Give me scalping signals for SOL 15-minute chart

# Directional bias
/signal Should I long or short ETH right now?

# Swing trading
/signal What's the swing trade setup for LINK?

# Entry/exit analysis
/signal Analyze XRP and give me entry and exit points

# Multiple assets
/signal Compare signals: BTC vs ETH vs SOL
```

## Features

- **Technical Indicator Analysis** - RSI, MACD, Bollinger Bands, Moving Averages, ATR, Volume
- **Chart Pattern Recognition** - Head & Shoulders, Triangles, Flags, Candlestick patterns
- **Multi-Timeframe Analysis** - 15m, 1H, 4H, Daily, Weekly confluence
- **Support/Resistance Levels** - Key levels and Fibonacci retracements
- **Signal Strength Rating** - Strong/Medium/Weak with confidence percentage
- **Entry/Exit Strategy** - Specific price levels for entries, stop-loss, take-profits
- **Risk Management** - Position sizing, risk/reward ratios, exposure calculations
- **Market Context** - Sentiment, correlation analysis, recent catalysts

## What It Analyzes

1. **Trend Indicators** - SMA, EMA, MACD, ADX
2. **Momentum Indicators** - RSI, Stochastic, CCI
3. **Volatility Indicators** - Bollinger Bands, ATR
4. **Volume Analysis** - OBV, volume profile, VWAP
5. **Chart Patterns** - Reversal and continuation patterns
6. **Support/Resistance** - Key levels, Fibonacci levels
7. **Multi-Timeframe** - Confluence across 5 timeframes
8. **Risk/Reward** - Position sizing and stop placement

## Output Includes

### Signal Summary
- Direction (Long/Short/Neutral)
- Strength (Strong/Medium/Weak)
- Timeframe (Scalp/Day/Swing/Position)
- Confidence percentage

### Technical Analysis
- Comprehensive indicator table
- Trend, momentum, volatility assessment
- Chart patterns identified
- Volume confirmation

### Trading Plan
- Aggressive and conservative entry prices
- Multiple take-profit targets
- Stop-loss placement
- Risk/reward ratio
- Position sizing calculation

### Risk Management
- Multi-timeframe confluence score
- Risk factors to consider
- Signal confirmation checklist
- Alternative scenarios

## Signal Strength Criteria

### Strong Signal (80-95% confidence)
- 3+ indicators align
- Volume confirms
- Multiple timeframes agree
- Clear chart pattern
- Near support/resistance

### Medium Signal (60-80% confidence)
- 2 indicators align
- Mixed timeframe signals
- Moderate volume
- Some confirmation

### Weak Signal (40-60% confidence)
- Single indicator
- Conflicting timeframes
- Low volume
- Choppy price action

## Trading Timeframes

### Scalping (15m - 1H)
- Quick in and out trades
- High frequency, small gains
- Tight stop losses
- High attention required

### Day Trading (1H - 4H)
- Intraday positions
- Close before end of day
- Medium stops
- Active monitoring

### Swing Trading (4H - Daily)
- Multi-day positions
- Capture larger moves
- Wider stops
- Periodic checking

### Position Trading (Daily - Weekly)
- Long-term holds
- Major trend following
- Wide stops
- Patient approach

## Key Indicators Explained

### RSI (Relative Strength Index)
Measures momentum. >70 overbought, <30 oversold.

### MACD (Moving Average Convergence Divergence)
Trend and momentum indicator. Crossovers signal entries.

### Bollinger Bands
Volatility bands. Price at extremes suggests reversal.

### Moving Averages
Trend direction. Golden/Death crosses signal major moves.

### ATR (Average True Range)
Volatility measure. Used for stop-loss placement.

## Risk Management Rules

### Position Sizing
Risk only 1-2% of account per trade.

### Stop-Loss Placement
- Support/resistance levels
- ATR-based (1.5x - 2x ATR)
- Percentage-based (2-5%)

### Take-Profit Targets
- Scale out at multiple levels
- Trail stop after TP1
- Lock in profits systematically

### Risk/Reward Ratio
Minimum 1:2 (risk $1 to make $2)
Ideal 1:3 or better

## Important Notes

- Technical analysis is probabilistic, not predictive
- No indicator is 100% accurate
- News and events override technical signals
- Crypto markets are highly volatile
- Always use stop losses
- Only trade with risk capital
- This generates educational analysis, not financial advice
- Do Your Own Research (DYOR)

## Data Sources

Analysis references:
- Technical indicator calculations (standard formulas)
- Chart pattern recognition principles
- Support/resistance identification
- Volume analysis methodologies
- Risk management best practices

## Requirements

- Asset pair (e.g., BTC/USDT)
- (Optional) Preferred timeframe
- (Optional) Directional bias
- (Optional) Account size for position sizing

## Files

- `commands/generate-signal.md` - Main signal generation command

## License

MIT License - See LICENSE file for details
