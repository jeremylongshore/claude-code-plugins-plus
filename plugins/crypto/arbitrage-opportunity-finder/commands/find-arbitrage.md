---
description: Find arbitrage opportunities across exchanges and DeFi protocols
shortcut: fa
---

# Find Arbitrage Opportunities

Scan for profitable arbitrage opportunities across CEX and DEX platforms with execution strategies.

## Implementation

```javascript
class ArbitrageFinder {
    async findOpportunities(params = {}) {
        const opportunities = [];

        // CEX arbitrage
        opportunities.push(...await this.findCEXArbitrage());

        // DEX arbitrage
        opportunities.push(...await this.findDEXArbitrage());

        // Cross-chain arbitrage
        opportunities.push(...await this.findCrossChainArbitrage());

        // Triangular arbitrage
        opportunities.push(...await this.findTriangularArbitrage());

        return opportunities.filter(opp => opp.profit > params.minProfit || 10);
    }

    async findCEXArbitrage() {
        const exchanges = ['binance', 'coinbase', 'kraken', 'ftx'];
        const opportunities = [];

        for (const pair of this.tradingPairs) {
            const prices = await this.fetchPricesFromExchanges(pair, exchanges);
            const spread = this.calculateSpread(prices);

            if (spread.percentage > 0.5) {
                opportunities.push({
                    type: 'CEX_ARBITRAGE',
                    pair,
                    buyExchange: spread.lowest.exchange,
                    sellExchange: spread.highest.exchange,
                    spread: spread.percentage,
                    profit: this.calculateProfit(spread, 10000),
                    executionTime: '< 1 minute',
                    risk: 'LOW'
                });
            }
        }

        return opportunities;
    }

    async findDEXArbitrage() {
        const dexes = ['uniswap', 'sushiswap', 'curve', 'balancer'];
        const opportunities = [];

        for (const token of this.tokens) {
            const prices = await this.fetchDEXPrices(token, dexes);
            const bestPath = this.findBestTradePath(prices);

            if (bestPath.profit > 50) {
                opportunities.push({
                    type: 'DEX_ARBITRAGE',
                    token,
                    path: bestPath.route,
                    profit: bestPath.profit,
                    gasEstimate: bestPath.gas,
                    netProfit: bestPath.profit - bestPath.gas,
                    risk: 'MEDIUM'
                });
            }
        }

        return opportunities;
    }

    calculateProfit(spread, capital) {
        const grossProfit = capital * (spread.percentage / 100);
        const fees = capital * 0.002; // 0.2% trading fees
        const slippage = capital * 0.001; // 0.1% slippage
        return grossProfit - fees - slippage;
    }
}
```

Find and analyze profitable arbitrage opportunities across markets.