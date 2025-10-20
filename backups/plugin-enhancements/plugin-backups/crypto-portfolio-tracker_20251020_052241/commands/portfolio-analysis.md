---
description: Analyze entire crypto portfolio with allocation, risk metrics, and rebalancing suggestions
shortcut: pa
---

# Portfolio Analysis

Comprehensive portfolio analysis for cryptocurrency holdings with advanced metrics, risk assessment, and optimization recommendations.

## Usage

Analyze the user's complete crypto portfolio to provide insights on:
- Asset allocation and diversification
- Risk metrics (Sharpe ratio, volatility, max drawdown)
- Performance attribution
- Correlation analysis
- Rebalancing recommendations

## Implementation

### 1. Portfolio Analytics Engine

```javascript
class PortfolioAnalyzer {
    constructor() {
        this.riskFreeRate = 0.02; // 2% annual risk-free rate
        this.historicalData = new Map();
        this.correlationMatrix = null;
    }

    async analyzePortfolio(positions) {
        // Fetch current prices and calculate values
        const portfolioData = await this.enrichPositions(positions);

        // Calculate core metrics
        const metrics = {
            totalValue: this.calculateTotalValue(portfolioData),
            totalCost: this.calculateTotalCost(portfolioData),
            totalPnL: this.calculateTotalPnL(portfolioData),
            allocation: this.calculateAllocation(portfolioData),
            concentration: this.calculateConcentration(portfolioData),
            volatility: await this.calculateVolatility(portfolioData),
            sharpeRatio: await this.calculateSharpeRatio(portfolioData),
            sortino: await this.calculateSortinoRatio(portfolioData),
            maxDrawdown: await this.calculateMaxDrawdown(portfolioData),
            correlations: await this.calculateCorrelations(portfolioData),
            var95: this.calculateValueAtRisk(portfolioData, 0.95),
            var99: this.calculateValueAtRisk(portfolioData, 0.99)
        };

        // Generate insights and recommendations
        const analysis = {
            metrics,
            riskAssessment: this.assessRisk(metrics),
            diversificationScore: this.calculateDiversificationScore(metrics),
            rebalancingPlan: this.generateRebalancingPlan(portfolioData, metrics),
            optimizations: this.suggestOptimizations(metrics)
        };

        return analysis;
    }

    calculateAllocation(portfolioData) {
        const totalValue = portfolioData.reduce((sum, p) => sum + p.currentValue, 0);

        return portfolioData.map(position => ({
            symbol: position.symbol,
            value: position.currentValue,
            percentage: (position.currentValue / totalValue) * 100,
            targetPercentage: position.targetAllocation || null,
            deviation: position.targetAllocation
                ? Math.abs(((position.currentValue / totalValue) * 100) - position.targetAllocation)
                : 0
        })).sort((a, b) => b.percentage - a.percentage);
    }

    calculateConcentration(portfolioData) {
        const allocations = this.calculateAllocation(portfolioData);
        const herfindahlIndex = allocations.reduce((sum, a) => {
            return sum + Math.pow(a.percentage / 100, 2);
        }, 0);

        return {
            herfindahlIndex: herfindahlIndex.toFixed(4),
            effectiveAssets: (1 / herfindahlIndex).toFixed(2),
            topAssetConcentration: allocations[0].percentage.toFixed(2),
            top3Concentration: allocations.slice(0, 3).reduce((sum, a) => sum + a.percentage, 0).toFixed(2)
        };
    }

    async calculateVolatility(portfolioData, period = 30) {
        const returns = await this.getHistoricalReturns(portfolioData, period);

        if (returns.length < 2) return null;

        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / (returns.length - 1);
        const volatility = Math.sqrt(variance);

        // Annualized volatility
        return {
            daily: (volatility * 100).toFixed(2),
            weekly: (volatility * Math.sqrt(7) * 100).toFixed(2),
            monthly: (volatility * Math.sqrt(30) * 100).toFixed(2),
            annual: (volatility * Math.sqrt(365) * 100).toFixed(2)
        };
    }

    async calculateSharpeRatio(portfolioData) {
        const returns = await this.getHistoricalReturns(portfolioData, 365);
        if (returns.length < 30) return null;

        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const annualizedReturn = avgReturn * 365;

        const stdDev = Math.sqrt(
            returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / (returns.length - 1)
        );
        const annualizedStdDev = stdDev * Math.sqrt(365);

        const sharpeRatio = (annualizedReturn - this.riskFreeRate) / annualizedStdDev;

        return {
            value: sharpeRatio.toFixed(3),
            interpretation: this.interpretSharpeRatio(sharpeRatio)
        };
    }

    interpretSharpeRatio(ratio) {
        if (ratio < 0) return 'POOR - Returns below risk-free rate';
        if (ratio < 0.5) return 'SUBOPTIMAL - Low risk-adjusted returns';
        if (ratio < 1.0) return 'ACCEPTABLE - Moderate risk-adjusted returns';
        if (ratio < 2.0) return 'GOOD - Strong risk-adjusted returns';
        return 'EXCELLENT - Outstanding risk-adjusted returns';
    }

    async calculateCorrelations(portfolioData) {
        if (portfolioData.length < 2) return null;

        const correlationMatrix = [];
        const symbols = portfolioData.map(p => p.symbol);

        for (let i = 0; i < symbols.length; i++) {
            const row = [];
            for (let j = 0; j < symbols.length; j++) {
                if (i === j) {
                    row.push(1.0);
                } else {
                    const correlation = await this.calculatePairCorrelation(
                        symbols[i],
                        symbols[j],
                        30 // 30-day correlation
                    );
                    row.push(correlation);
                }
            }
            correlationMatrix.push(row);
        }

        // Find highest correlations
        const highCorrelations = [];
        for (let i = 0; i < symbols.length; i++) {
            for (let j = i + 1; j < symbols.length; j++) {
                if (Math.abs(correlationMatrix[i][j]) > 0.7) {
                    highCorrelations.push({
                        pair: `${symbols[i]}-${symbols[j]}`,
                        correlation: correlationMatrix[i][j].toFixed(3),
                        interpretation: correlationMatrix[i][j] > 0 ? 'POSITIVE' : 'NEGATIVE'
                    });
                }
            }
        }

        return {
            matrix: correlationMatrix,
            symbols,
            highCorrelations,
            averageCorrelation: this.calculateAverageCorrelation(correlationMatrix)
        };
    }

    calculateValueAtRisk(portfolioData, confidenceLevel) {
        const returns = this.historicalData.get('portfolio_returns') || [];
        if (returns.length < 100) return null;

        const sortedReturns = returns.sort((a, b) => a - b);
        const index = Math.floor((1 - confidenceLevel) * sortedReturns.length);
        const var_value = sortedReturns[index];
        const totalValue = portfolioData.reduce((sum, p) => sum + p.currentValue, 0);

        return {
            percentage: (var_value * 100).toFixed(2),
            dollarAmount: (totalValue * var_value).toFixed(2),
            confidenceLevel: (confidenceLevel * 100).toFixed(0),
            interpretation: `${confidenceLevel * 100}% chance that losses won't exceed $${Math.abs(totalValue * var_value).toFixed(2)}`
        };
    }

    assessRisk(metrics) {
        const riskFactors = [];
        let riskScore = 0;

        // Concentration risk
        if (metrics.concentration.topAssetConcentration > 50) {
            riskFactors.push({
                type: 'CONCENTRATION',
                severity: 'HIGH',
                description: `Top asset represents ${metrics.concentration.topAssetConcentration}% of portfolio`
            });
            riskScore += 30;
        }

        // Volatility risk
        if (metrics.volatility && metrics.volatility.annual > 100) {
            riskFactors.push({
                type: 'VOLATILITY',
                severity: 'HIGH',
                description: `Annual volatility exceeds 100% (${metrics.volatility.annual}%)`
            });
            riskScore += 25;
        }

        // Correlation risk
        if (metrics.correlations && metrics.correlations.highCorrelations.length > 0) {
            riskFactors.push({
                type: 'CORRELATION',
                severity: 'MEDIUM',
                description: `${metrics.correlations.highCorrelations.length} asset pairs highly correlated`
            });
            riskScore += 15;
        }

        // Drawdown risk
        if (metrics.maxDrawdown && metrics.maxDrawdown.percentage > 40) {
            riskFactors.push({
                type: 'DRAWDOWN',
                severity: 'HIGH',
                description: `Maximum drawdown of ${metrics.maxDrawdown.percentage}% observed`
            });
            riskScore += 20;
        }

        return {
            overallScore: Math.min(riskScore, 100),
            level: this.determineRiskLevel(riskScore),
            factors: riskFactors,
            recommendations: this.generateRiskRecommendations(riskFactors)
        };
    }

    determineRiskLevel(score) {
        if (score < 20) return 'LOW';
        if (score < 40) return 'MODERATE';
        if (score < 60) return 'ELEVATED';
        if (score < 80) return 'HIGH';
        return 'CRITICAL';
    }

    generateRebalancingPlan(portfolioData, metrics) {
        const currentAllocations = metrics.allocation;
        const targetAllocations = this.calculateOptimalAllocation(portfolioData, metrics);
        const totalValue = metrics.totalValue;

        const rebalancingActions = [];

        currentAllocations.forEach((current, index) => {
            const target = targetAllocations[index];
            const currentValue = current.value;
            const targetValue = (target.percentage / 100) * totalValue;
            const difference = targetValue - currentValue;

            if (Math.abs(difference) > totalValue * 0.01) { // Only rebalance if > 1% of portfolio
                rebalancingActions.push({
                    symbol: current.symbol,
                    action: difference > 0 ? 'BUY' : 'SELL',
                    amount: Math.abs(difference).toFixed(2),
                    currentPercentage: current.percentage.toFixed(2),
                    targetPercentage: target.percentage.toFixed(2),
                    reason: target.reason
                });
            }
        });

        return {
            actions: rebalancingActions,
            estimatedCost: this.estimateRebalancingCost(rebalancingActions),
            expectedImprovement: this.estimateImprovementMetrics(targetAllocations, currentAllocations)
        };
    }

    calculateOptimalAllocation(portfolioData, metrics) {
        // Modern Portfolio Theory optimization
        // This is a simplified version - real implementation would use quadratic programming

        const riskTolerance = this.determineRiskTolerance(metrics);
        const correlations = metrics.correlations?.matrix || [];

        // Start with equal weight
        let allocations = portfolioData.map(p => ({
            symbol: p.symbol,
            percentage: 100 / portfolioData.length,
            reason: 'Equal weight baseline'
        }));

        // Adjust based on performance
        allocations = this.adjustForPerformance(allocations, portfolioData);

        // Adjust based on risk
        allocations = this.adjustForRisk(allocations, metrics, riskTolerance);

        // Adjust based on correlations
        if (correlations.length > 0) {
            allocations = this.adjustForCorrelations(allocations, correlations);
        }

        // Apply constraints
        allocations = this.applyAllocationConstraints(allocations);

        return allocations;
    }

    adjustForPerformance(allocations, portfolioData) {
        // Increase allocation to better performers
        const performances = portfolioData.map(p => ({
            symbol: p.symbol,
            performance: p.pnlPercentage
        })).sort((a, b) => b.performance - a.performance);

        return allocations.map(alloc => {
            const perf = performances.find(p => p.symbol === alloc.symbol);
            const rank = performances.indexOf(perf);

            // Top 1/3 get boost, bottom 1/3 get reduction
            if (rank < performances.length / 3) {
                alloc.percentage *= 1.2;
                alloc.reason = 'Strong performance';
            } else if (rank > (performances.length * 2 / 3)) {
                alloc.percentage *= 0.8;
                alloc.reason = 'Weak performance';
            }

            return alloc;
        });
    }

    applyAllocationConstraints(allocations) {
        // No single asset > 40%
        const maxAllocation = 40;
        // No single asset < 5%
        const minAllocation = 5;

        // Normalize to ensure sum = 100
        const total = allocations.reduce((sum, a) => sum + a.percentage, 0);
        allocations = allocations.map(a => ({
            ...a,
            percentage: (a.percentage / total) * 100
        }));

        // Apply constraints
        allocations = allocations.map(alloc => ({
            ...alloc,
            percentage: Math.min(Math.max(alloc.percentage, minAllocation), maxAllocation)
        }));

        // Re-normalize
        const newTotal = allocations.reduce((sum, a) => sum + a.percentage, 0);
        return allocations.map(a => ({
            ...a,
            percentage: (a.percentage / newTotal) * 100
        }));
    }
}
```

### 2. Portfolio Visualization

```javascript
class PortfolioVisualizer {
    generateReport(analysis) {
        return `
╔════════════════════════════════════════════════════════════════════════════╗
║                          PORTFOLIO ANALYSIS REPORT                         ║
╠════════════════════════════════════════════════════════════════════════════╣
║                              SUMMARY METRICS                               ║
╠════════════════════════════════════════════════════════════════════════════╣
║ Total Value:        $${analysis.metrics.totalValue.toFixed(2).padEnd(55)} ║
║ Total Cost:         $${analysis.metrics.totalCost.toFixed(2).padEnd(55)} ║
║ Total P&L:          ${this.formatPnL(analysis.metrics.totalPnL).padEnd(56)} ║
║ Total Return:       ${this.formatPercentage(analysis.metrics.totalReturn).padEnd(56)} ║
╠════════════════════════════════════════════════════════════════════════════╣
║                             RISK METRICS                                   ║
╠════════════════════════════════════════════════════════════════════════════╣
║ Risk Level:         ${analysis.riskAssessment.level.padEnd(56)} ║
║ Risk Score:         ${(analysis.riskAssessment.overallScore + '/100').padEnd(56)} ║
║ Sharpe Ratio:       ${analysis.metrics.sharpeRatio?.value || 'N/A'.padEnd(56)} ║
║ Annual Volatility:  ${analysis.metrics.volatility?.annual + '%' || 'N/A'.padEnd(56)} ║
║ Max Drawdown:       ${analysis.metrics.maxDrawdown?.percentage + '%' || 'N/A'.padEnd(56)} ║
║ VaR (95%):         ${analysis.metrics.var95?.dollarAmount || 'N/A'.padEnd(56)} ║
╠════════════════════════════════════════════════════════════════════════════╣
║                            ASSET ALLOCATION                                ║
╠════════════════════════════════════════════════════════════════════════════╣
${this.formatAllocationTable(analysis.metrics.allocation)}
╠════════════════════════════════════════════════════════════════════════════╣
║                          CONCENTRATION ANALYSIS                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║ Herfindahl Index:   ${analysis.metrics.concentration.herfindahlIndex.padEnd(56)} ║
║ Effective Assets:   ${analysis.metrics.concentration.effectiveAssets.padEnd(56)} ║
║ Top Asset:          ${analysis.metrics.concentration.topAssetConcentration + '%'.padEnd(56)} ║
║ Top 3 Assets:       ${analysis.metrics.concentration.top3Concentration + '%'.padEnd(56)} ║
╠════════════════════════════════════════════════════════════════════════════╣
║                         REBALANCING RECOMMENDATIONS                        ║
╠════════════════════════════════════════════════════════════════════════════╣
${this.formatRebalancingActions(analysis.rebalancingPlan.actions)}
╠════════════════════════════════════════════════════════════════════════════╣
║                            RISK FACTORS                                    ║
╠════════════════════════════════════════════════════════════════════════════╣
${this.formatRiskFactors(analysis.riskAssessment.factors)}
╚════════════════════════════════════════════════════════════════════════════╝
        `;
    }

    formatAllocationTable(allocations) {
        return allocations.slice(0, 5).map(a =>
            `║ ${a.symbol.padEnd(10)} ${(a.percentage.toFixed(2) + '%').padEnd(10)} $${a.value.toFixed(2).padEnd(15)} ${this.getAllocationBar(a.percentage).padEnd(20)} ║`
        ).join('\n');
    }

    getAllocationBar(percentage) {
        const barLength = Math.floor(percentage / 5);
        return '█'.repeat(Math.min(barLength, 20));
    }

    formatRebalancingActions(actions) {
        if (actions.length === 0) {
            return '║ Portfolio is well-balanced. No actions required.                          ║';
        }

        return actions.slice(0, 3).map(a =>
            `║ ${a.action.padEnd(5)} ${a.symbol.padEnd(6)} $${a.amount.padEnd(10)} (${a.currentPercentage}% → ${a.targetPercentage}%)`.padEnd(77) + '║'
        ).join('\n');
    }

    formatRiskFactors(factors) {
        if (factors.length === 0) {
            return '║ No significant risk factors identified.                                   ║';
        }

        return factors.map(f =>
            `║ [${f.severity}] ${f.type}: ${f.description}`.padEnd(77) + '║'
        ).join('\n');
    }

    formatPnL(value) {
        const formatted = `$${Math.abs(value).toFixed(2)}`;
        return value >= 0 ? `+${formatted} ` : `-${formatted} `;
    }

    formatPercentage(value) {
        const formatted = `${Math.abs(value).toFixed(2)}%`;
        return value >= 0 ? `+${formatted} ` : `-${formatted} `;
    }
}
```

### 3. Optimization Strategies

```javascript
class PortfolioOptimizer {
    suggestOptimizations(metrics) {
        const suggestions = [];

        // Diversification suggestions
        if (metrics.concentration.effectiveAssets < 3) {
            suggestions.push({
                priority: 'HIGH',
                category: 'DIVERSIFICATION',
                action: 'Add more uncorrelated assets',
                benefit: 'Reduce concentration risk by 30-40%',
                implementation: `
                    Consider adding:
                    - Large cap altcoins (ETH, BNB) if heavily in BTC
                    - DeFi tokens if heavily in L1s
                    - Stablecoins for risk reduction
                `
            });
        }

        // Rebalancing suggestions
        if (metrics.allocation.some(a => a.deviation > 10)) {
            suggestions.push({
                priority: 'MEDIUM',
                category: 'REBALANCING',
                action: 'Rebalance to target allocations',
                benefit: 'Improve risk-adjusted returns',
                implementation: `
                    Set up periodic rebalancing:
                    - Monthly for volatile markets
                    - Quarterly for stable markets
                    - Threshold-based (when deviation > 15%)
                `
            });
        }

        // Risk management suggestions
        if (!metrics.stopLossesSet) {
            suggestions.push({
                priority: 'HIGH',
                category: 'RISK_MANAGEMENT',
                action: 'Implement stop-loss orders',
                benefit: 'Limit downside risk',
                implementation: `
                    Recommended stop-loss levels:
                    - Conservative: 15% below entry
                    - Moderate: 25% below entry
                    - Aggressive: 35% below entry
                `
            });
        }

        // Performance suggestions
        if (metrics.sharpeRatio && metrics.sharpeRatio.value < 0.5) {
            suggestions.push({
                priority: 'MEDIUM',
                category: 'PERFORMANCE',
                action: 'Improve risk-adjusted returns',
                benefit: 'Better Sharpe ratio',
                implementation: `
                    Options to improve:
                    - Reduce allocation to high-volatility assets
                    - Add yield-generating positions (staking, lending)
                    - Consider market-neutral strategies
                `
            });
        }

        return suggestions;
    }
}
```

## Error Handling

```javascript
async function executePortfolioAnalysis() {
    try {
        const analyzer = new PortfolioAnalyzer();
        const visualizer = new PortfolioVisualizer();

        // Get all open positions
        const positions = await getOpenPositions();

        if (positions.length === 0) {
            console.log('No positions found. Start by tracking some positions first.');
            return;
        }

        // Run analysis
        console.log('Analyzing portfolio...');
        const analysis = await analyzer.analyzePortfolio(positions);

        // Display report
        const report = visualizer.generateReport(analysis);
        console.log(report);

        // Save analysis
        await saveAnalysis(analysis);

    } catch (error) {
        console.error('Portfolio analysis failed:', error.message);

        if (error.code === 'INSUFFICIENT_DATA') {
            console.log('Not enough historical data for full analysis. Some metrics may be unavailable.');
        } else if (error.code === 'API_ERROR') {
            console.log('Failed to fetch market data. Please check your internet connection.');
        }
    }
}
```

This comprehensive portfolio analysis command provides institutional-grade analytics for crypto portfolios with actionable insights and optimization recommendations.