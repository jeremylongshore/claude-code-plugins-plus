---
description: Backtest trading strategies with historical data and comprehensive performance analysis
shortcut: bs
---

# Backtest Trading Strategy

Test trading strategies against historical data with performance metrics, risk analysis, and optimization.

## Usage

Implement comprehensive backtesting with:

### Parameters
- **Strategy**: Type of strategy to test
- **Symbol**: Asset or portfolio to test
- **Period**: Historical timeframe
- **Initial Capital**: Starting amount
- **Parameters**: Strategy-specific settings

## Implementation

```javascript
class StrategyBacktester {
    constructor() {
        this.strategies = {
            movingAverage: new MovingAverageStrategy(),
            rsi: new RSIStrategy(),
            macd: new MACDStrategy(),
            breakout: new BreakoutStrategy(),
            meanReversion: new MeanReversionStrategy(),
            momentum: new MomentumStrategy(),
            pairs: new PairsTrading(),
            gridTrading: new GridTradingStrategy()
        };
    }

    async backtest(params) {
        const {
            strategy = 'movingAverage',
            symbol = 'BTC/USDT',
            period = '1y',
            capital = 10000,
            parameters = {}
        } = params;

        // Fetch historical data
        const data = await this.fetchHistoricalData(symbol, period);

        // Run strategy
        const trades = await this.runStrategy(
            this.strategies[strategy],
            data,
            parameters
        );

        // Calculate metrics
        const performance = this.calculatePerformance(trades, capital);
        const risk = this.calculateRiskMetrics(trades, data);

        // Optimization
        const optimized = await this.optimizeParameters(
            strategy,
            data,
            parameters
        );

        return {
            summary: this.generateSummary(performance, risk),
            trades,
            performance,
            risk,
            optimized,
            equity: this.calculateEquityCurve(trades, capital)
        };
    }

    async runStrategy(strategy, data, params) {
        const trades = [];
        let position = null;

        for (let i = strategy.lookback; i < data.length; i++) {
            const slice = data.slice(0, i + 1);
            const signals = strategy.generateSignals(slice, params);

            if (!position && signals.entry) {
                position = {
                    type: signals.type,
                    entryPrice: data[i].close,
                    entryTime: data[i].timestamp,
                    size: signals.size || 1
                };
            }

            if (position && signals.exit) {
                trades.push({
                    ...position,
                    exitPrice: data[i].close,
                    exitTime: data[i].timestamp,
                    pnl: this.calculatePnL(position, data[i].close),
                    duration: data[i].timestamp - position.entryTime
                });
                position = null;
            }
        }

        return trades;
    }

    calculatePerformance(trades, capital) {
        let equity = capital;
        const returns = [];

        for (const trade of trades) {
            const returnPct = trade.pnl / equity;
            returns.push(returnPct);
            equity += trade.pnl;
        }

        return {
            totalReturn: ((equity - capital) / capital) * 100,
            winRate: trades.filter(t => t.pnl > 0).length / trades.length * 100,
            avgWin: this.average(trades.filter(t => t.pnl > 0).map(t => t.pnl)),
            avgLoss: this.average(trades.filter(t => t.pnl < 0).map(t => Math.abs(t.pnl))),
            profitFactor: this.calculateProfitFactor(trades),
            sharpeRatio: this.calculateSharpe(returns),
            maxDrawdown: this.calculateMaxDrawdown(trades, capital),
            calmarRatio: this.calculateCalmar(returns),
            totalTrades: trades.length
        };
    }

    calculateRiskMetrics(trades, data) {
        return {
            var95: this.calculateVaR(trades, 0.95),
            cvar95: this.calculateCVaR(trades, 0.95),
            maxConsecutiveLosses: this.maxConsecutiveLosses(trades),
            recoveryFactor: this.calculateRecoveryFactor(trades),
            ulcerIndex: this.calculateUlcerIndex(trades),
            sortinoRatio: this.calculateSortino(trades)
        };
    }
}

class MovingAverageStrategy {
    lookback = 200;

    generateSignals(data, params) {
        const { fast = 50, slow = 200 } = params;

        if (data.length < slow) return {};

        const fastMA = this.sma(data.slice(-fast), fast);
        const slowMA = this.sma(data.slice(-slow), slow);
        const prevFastMA = this.sma(data.slice(-fast - 1, -1), fast);
        const prevSlowMA = this.sma(data.slice(-slow - 1, -1), slow);

        // Golden cross
        if (prevFastMA < prevSlowMA && fastMA > slowMA) {
            return { entry: true, type: 'LONG', size: 1 };
        }

        // Death cross
        if (prevFastMA > prevSlowMA && fastMA < slowMA) {
            return { exit: true };
        }

        return {};
    }

    sma(data, period) {
        return data.reduce((sum, d) => sum + d.close, 0) / period;
    }
}

// Display results
class BacktestDisplay {
    display(results) {
        return `
╔════════════════════════════════════════════════════════════════╗
║                   STRATEGY BACKTEST RESULTS                    ║
╠════════════════════════════════════════════════════════════════╣
${this.formatSummary(results.summary)}
╠════════════════════════════════════════════════════════════════╣
║                    PERFORMANCE METRICS                         ║
╠════════════════════════════════════════════════════════════════╣
${this.formatPerformance(results.performance)}
╠════════════════════════════════════════════════════════════════╣
║                      RISK METRICS                              ║
╠════════════════════════════════════════════════════════════════╣
${this.formatRisk(results.risk)}
╠════════════════════════════════════════════════════════════════╣
║                   TRADE DISTRIBUTION                           ║
╠════════════════════════════════════════════════════════════════╣
${this.formatDistribution(results.trades)}
╚════════════════════════════════════════════════════════════════╝
`;
    }
}
```

This provides comprehensive strategy backtesting with performance analysis and risk metrics.