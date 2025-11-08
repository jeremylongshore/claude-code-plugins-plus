---
description: Track crypto positions with entry prices, current values, and PnL calculations
shortcut: tp
---

# Track Crypto Position

Comprehensive position tracking for cryptocurrency investments with real-time price updates and advanced analytics.

## Usage

When the user wants to track a crypto position, gather the following information and implement a complete tracking system:

### Required Information
- **Symbol**: The cryptocurrency ticker (BTC, ETH, SOL, etc.)
- **Entry Price**: Purchase price per unit
- **Quantity**: Amount purchased
- **Entry Date**: When the position was opened
- **Exchange**: Where the trade was executed (optional)
- **Target Price**: Profit target (optional)
- **Stop Loss**: Risk management level (optional)

## Implementation

### 1. Database Schema

Create a structured database to track positions:

```sql
CREATE TABLE IF NOT EXISTS crypto_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    entry_date TIMESTAMP NOT NULL,
    current_price DECIMAL(20,8),
    last_updated TIMESTAMP,
    exchange VARCHAR(50),
    target_price DECIMAL(20,8),
    stop_loss DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'open',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS position_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID REFERENCES crypto_positions(id),
    price DECIMAL(20,8) NOT NULL,
    value DECIMAL(20,8) NOT NULL,
    pnl DECIMAL(20,8) NOT NULL,
    pnl_percentage DECIMAL(10,4) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_symbol ON crypto_positions(symbol);
CREATE INDEX idx_positions_status ON crypto_positions(status);
CREATE INDEX idx_history_position ON position_history(position_id);
```

### 2. Position Tracking Class

```javascript
class CryptoPositionTracker {
    constructor() {
        this.priceFeeds = {
            coingecko: 'https://api.coingecko.com/api/v3',
            binance: 'https://api.binance.com/api/v3',
            coinbase: 'https://api.coinbase.com/v2'
        };
    }

    async trackPosition(positionData) {
        const {
            symbol,
            entryPrice,
            quantity,
            entryDate,
            exchange = 'Unknown',
            targetPrice = null,
            stopLoss = null,
            notes = ''
        } = positionData;

        // Validate input
        this.validatePositionData(positionData);

        // Get current price
        const currentPrice = await this.getCurrentPrice(symbol);

        // Calculate metrics
        const metrics = this.calculateMetrics({
            entryPrice,
            quantity,
            currentPrice
        });

        // Store position
        const position = await this.storePosition({
            symbol: symbol.toUpperCase(),
            entry_price: entryPrice,
            quantity,
            entry_date: entryDate,
            current_price: currentPrice,
            exchange,
            target_price: targetPrice,
            stop_loss: stopLoss,
            notes
        });

        // Record initial history
        await this.recordHistory(position.id, currentPrice, metrics);

        return {
            position,
            metrics,
            analysis: this.analyzePosition(position, metrics)
        };
    }

    calculateMetrics({ entryPrice, quantity, currentPrice }) {
        const entryValue = entryPrice * quantity;
        const currentValue = currentPrice * quantity;
        const unrealizedPnL = currentValue - entryValue;
        const pnlPercentage = ((currentValue - entryValue) / entryValue) * 100;

        return {
            entryValue: parseFloat(entryValue.toFixed(2)),
            currentValue: parseFloat(currentValue.toFixed(2)),
            unrealizedPnL: parseFloat(unrealizedPnL.toFixed(2)),
            pnlPercentage: parseFloat(pnlPercentage.toFixed(2)),
            roi: pnlPercentage,
            riskRewardRatio: this.calculateRiskReward({
                entryPrice,
                currentPrice,
                targetPrice: position.target_price,
                stopLoss: position.stop_loss
            })
        };
    }

    calculateRiskReward({ entryPrice, currentPrice, targetPrice, stopLoss }) {
        if (!targetPrice || !stopLoss) return null;

        const potentialReward = targetPrice - entryPrice;
        const potentialRisk = entryPrice - stopLoss;

        if (potentialRisk === 0) return null;

        return parseFloat((potentialReward / potentialRisk).toFixed(2));
    }

    analyzePosition(position, metrics) {
        const analysis = {
            status: this.determineStatus(metrics),
            recommendation: this.getRecommendation(position, metrics),
            risks: this.identifyRisks(position, metrics),
            opportunities: this.identifyOpportunities(position, metrics)
        };

        return analysis;
    }

    determineStatus(metrics) {
        if (metrics.pnlPercentage > 20) return 'STRONG_PROFIT';
        if (metrics.pnlPercentage > 5) return 'PROFIT';
        if (metrics.pnlPercentage > -5) return 'NEUTRAL';
        if (metrics.pnlPercentage > -20) return 'LOSS';
        return 'SIGNIFICANT_LOSS';
    }

    getRecommendation(position, metrics) {
        const recommendations = [];

        // Check stop loss
        if (position.stop_loss && position.current_price <= position.stop_loss) {
            recommendations.push({
                action: 'EXIT',
                reason: 'Stop loss hit',
                urgency: 'HIGH'
            });
        }

        // Check target
        if (position.target_price && position.current_price >= position.target_price) {
            recommendations.push({
                action: 'TAKE_PROFIT',
                reason: 'Target price reached',
                urgency: 'MEDIUM'
            });
        }

        // Check significant profit
        if (metrics.pnlPercentage > 50) {
            recommendations.push({
                action: 'PARTIAL_PROFIT',
                reason: 'Consider taking partial profits (50%+ gain)',
                urgency: 'LOW'
            });
        }

        // Check significant loss
        if (metrics.pnlPercentage < -30 && !position.stop_loss) {
            recommendations.push({
                action: 'SET_STOP_LOSS',
                reason: 'Significant loss without stop loss protection',
                urgency: 'HIGH'
            });
        }

        return recommendations;
    }

    async getCurrentPrice(symbol) {
        // Implementation would fetch from multiple sources
        // and return average or most reliable price
        try {
            const prices = await Promise.all([
                this.fetchCoingeckoPrice(symbol),
                this.fetchBinancePrice(symbol)
            ]);

            return prices.reduce((sum, price) => sum + price, 0) / prices.length;
        } catch (error) {
            throw new Error(`Failed to fetch price for ${symbol}: ${error.message}`);
        }
    }

    async updateAllPositions() {
        const openPositions = await this.getOpenPositions();
        const updates = [];

        for (const position of openPositions) {
            try {
                const currentPrice = await this.getCurrentPrice(position.symbol);
                const metrics = this.calculateMetrics({
                    entryPrice: position.entry_price,
                    quantity: position.quantity,
                    currentPrice
                });

                await this.updatePosition(position.id, {
                    current_price: currentPrice,
                    last_updated: new Date()
                });

                await this.recordHistory(position.id, currentPrice, metrics);

                updates.push({
                    symbol: position.symbol,
                    currentPrice,
                    metrics,
                    status: 'UPDATED'
                });
            } catch (error) {
                updates.push({
                    symbol: position.symbol,
                    status: 'ERROR',
                    error: error.message
                });
            }
        }

        return updates;
    }
}
```

### 3. Display Format

When displaying position information, format it clearly:

```javascript
function displayPosition(position, metrics) {
    const output = `
╔════════════════════════════════════════════════════════════════╗
║                    CRYPTO POSITION TRACKER                     ║
╠════════════════════════════════════════════════════════════════╣
║ Symbol:        ${position.symbol.padEnd(48)} ║
║ Entry Price:   $${position.entry_price.toFixed(2).padEnd(47)} ║
║ Current Price: $${position.current_price.toFixed(2).padEnd(47)} ║
║ Quantity:      ${position.quantity.toString().padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                          METRICS                               ║
╠════════════════════════════════════════════════════════════════╣
║ Entry Value:   $${metrics.entryValue.toFixed(2).padEnd(47)} ║
║ Current Value: $${metrics.currentValue.toFixed(2).padEnd(47)} ║
║ Unrealized P&L: ${formatPnL(metrics.unrealizedPnL).padEnd(47)} ║
║ P&L %:         ${formatPnLPercentage(metrics.pnlPercentage).padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║ Status:        ${determineStatusEmoji(metrics.pnlPercentage)} ${metrics.status.padEnd(43)} ║
╚════════════════════════════════════════════════════════════════╝
    `;

    return output;
}

function formatPnL(value) {
    const formatted = `$${Math.abs(value).toFixed(2)}`;
    if (value >= 0) {
        return `+${formatted} `;
    } else {
        return `-${formatted} `;
    }
}

function formatPnLPercentage(percentage) {
    const formatted = `${Math.abs(percentage).toFixed(2)}%`;
    if (percentage >= 0) {
        return `+${formatted} `;
    } else {
        return `-${formatted} `;
    }
}

function determineStatusEmoji(percentage) {
    if (percentage > 20) return '';
    if (percentage > 5) return '';
    if (percentage > -5) return '';
    if (percentage > -20) return '️';
    return '';
}
```

### 4. Alert System

Set up automatic alerts for significant events:

```javascript
class PositionAlertSystem {
    constructor() {
        this.alertThresholds = {
            profitTarget: 0.20,      // 20% profit
            lossWarning: -0.10,      // 10% loss
            criticalLoss: -0.25,     // 25% loss
            volatilitySpike: 0.15    // 15% daily move
        };
    }

    async checkAlerts(position, previousPrice, currentPrice) {
        const alerts = [];
        const priceChange = ((currentPrice - previousPrice) / previousPrice) * 100;

        // Check profit targets
        if (metrics.pnlPercentage >= this.alertThresholds.profitTarget * 100) {
            alerts.push({
                type: 'PROFIT_TARGET',
                message: ` ${position.symbol} hit profit target: +${metrics.pnlPercentage.toFixed(2)}%`,
                severity: 'INFO',
                action: 'Consider taking profits'
            });
        }

        // Check loss warnings
        if (metrics.pnlPercentage <= this.alertThresholds.lossWarning * 100 &&
            metrics.pnlPercentage > this.alertThresholds.criticalLoss * 100) {
            alerts.push({
                type: 'LOSS_WARNING',
                message: `️ ${position.symbol} loss warning: ${metrics.pnlPercentage.toFixed(2)}%`,
                severity: 'WARNING',
                action: 'Review position and consider stop loss'
            });
        }

        // Check critical loss
        if (metrics.pnlPercentage <= this.alertThresholds.criticalLoss * 100) {
            alerts.push({
                type: 'CRITICAL_LOSS',
                message: ` ${position.symbol} critical loss: ${metrics.pnlPercentage.toFixed(2)}%`,
                severity: 'CRITICAL',
                action: 'Immediate review required'
            });
        }

        // Check volatility
        if (Math.abs(priceChange) >= this.alertThresholds.volatilitySpike * 100) {
            alerts.push({
                type: 'VOLATILITY_SPIKE',
                message: ` ${position.symbol} volatility spike: ${priceChange > 0 ? '+' : ''}${priceChange.toFixed(2)}% in 24h`,
                severity: 'INFO',
                action: 'Monitor closely for opportunities or risks'
            });
        }

        return alerts;
    }
}
```

## Error Handling

Always implement comprehensive error handling:

```javascript
try {
    const position = await tracker.trackPosition({
        symbol: 'BTC',
        entryPrice: 45000,
        quantity: 0.5,
        entryDate: new Date('2024-01-01'),
        targetPrice: 60000,
        stopLoss: 40000
    });

    displayPosition(position.position, position.metrics);
} catch (error) {
    if (error.code === 'INVALID_SYMBOL') {
        console.error(`Invalid cryptocurrency symbol: ${error.symbol}`);
    } else if (error.code === 'API_ERROR') {
        console.error(`Failed to fetch price data: ${error.message}`);
    } else {
        console.error(`Unexpected error: ${error.message}`);
    }
}
```

This command provides comprehensive position tracking with real-time updates, PnL calculations, risk analysis, and actionable recommendations for crypto investments.