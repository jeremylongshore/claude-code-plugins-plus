# Trading Strategy Backtester Plugin

Comprehensive backtesting framework for trading strategies with historical data analysis, performance metrics, and parameter optimization.

## Features

###  Strategy Library
- Moving Average Crossover
- RSI Overbought/Oversold
- MACD Signal Line
- Breakout Trading
- Mean Reversion
- Momentum Trading
- Pairs Trading
- Grid Trading

###  Performance Metrics
- Total Return & Win Rate
- Sharpe & Sortino Ratios
- Maximum Drawdown
- Profit Factor
- Calmar Ratio
- Recovery Factor

###  Risk Analysis
- Value at Risk (VaR)
- Conditional VaR
- Consecutive Losses
- Ulcer Index
- Risk-Adjusted Returns

## Installation

```bash
/plugin install trading-strategy-backtester@claude-code-plugins-plus
```

## Usage

```
/backtest-strategy

Testing moving average strategy:
- Symbol: BTC/USDT
- Period: 1 year
- Capital: $10,000
- Parameters: 50/200 MA
```

## Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/backtest-strategy` | Run backtest | `bs` |
| `/optimize-parameters` | Parameter optimization | `op` |
| `/compare-strategies` | Strategy comparison | `cs` |
| `/walk-forward` | Walk-forward analysis | `wf` |

## Strategies

### Moving Average
- Golden/Death Cross signals
- Customizable periods
- Multiple MA types

### RSI Strategy
- Oversold/Overbought levels
- Divergence detection
- Dynamic thresholds

### MACD Strategy
- Signal line crossovers
- Histogram analysis
- Zero-line crosses

## License

MIT License

---

*Built for traders by Intent Solutions IO*