---
description: Track crypto wallets across multiple chains with real-time balance and transaction monitoring
shortcut: tw
---

# Track Wallet Portfolio

Monitor crypto wallets across chains with portfolio analytics, DeFi positions, and transaction history.

## Implementation

```javascript
class WalletPortfolioTracker {
    constructor() {
        this.chains = {
            ethereum: { explorer: 'etherscan.io', rpc: process.env.ETH_RPC },
            bsc: { explorer: 'bscscan.com', rpc: process.env.BSC_RPC },
            polygon: { explorer: 'polygonscan.com', rpc: process.env.POLYGON_RPC },
            arbitrum: { explorer: 'arbiscan.io', rpc: process.env.ARB_RPC },
            avalanche: { explorer: 'snowtrace.io', rpc: process.env.AVAX_RPC }
        };
    }

    async trackWallet(address, options = {}) {
        const portfolio = {
            address,
            timestamp: Date.now(),
            totalValue: 0,
            chains: {},
            tokens: [],
            nfts: [],
            defi: [],
            transactions: []
        };

        // Scan all chains
        for (const [chain, config] of Object.entries(this.chains)) {
            const chainData = await this.scanChain(address, chain, config);
            portfolio.chains[chain] = chainData;
            portfolio.totalValue += chainData.value;
        }

        // Aggregate tokens
        portfolio.tokens = this.aggregateTokens(portfolio.chains);

        // Fetch DeFi positions
        portfolio.defi = await this.scanDeFiPositions(address);

        // Get recent transactions
        portfolio.transactions = await this.getRecentTransactions(address);

        // Calculate analytics
        portfolio.analytics = this.calculateAnalytics(portfolio);

        return portfolio;
    }

    async scanChain(address, chain, config) {
        const balances = await this.getTokenBalances(address, chain);
        const nativeBalance = await this.getNativeBalance(address, chain);

        return {
            chain,
            nativeBalance,
            tokens: balances,
            value: this.calculateChainValue(nativeBalance, balances),
            protocols: await this.getProtocolPositions(address, chain)
        };
    }

    async scanDeFiPositions(address) {
        const positions = [];

        // Lending protocols
        positions.push(...await this.scanLending(address));

        // DEX LP positions
        positions.push(...await this.scanLiquidityPools(address));

        // Yield farms
        positions.push(...await this.scanYieldFarms(address));

        // Staking
        positions.push(...await this.scanStaking(address));

        return positions;
    }

    calculateAnalytics(portfolio) {
        return {
            diversification: this.calculateDiversification(portfolio.tokens),
            chainDistribution: this.getChainDistribution(portfolio.chains),
            topHoldings: portfolio.tokens.slice(0, 10),
            riskScore: this.calculateRiskScore(portfolio),
            defiExposure: portfolio.defi.reduce((sum, p) => sum + p.value, 0),
            gasSpent: this.calculateGasSpent(portfolio.transactions)
        };
    }

    async getRecentTransactions(address, limit = 50) {
        const txs = [];

        for (const chain of Object.keys(this.chains)) {
            const chainTxs = await this.fetchTransactions(address, chain, limit);
            txs.push(...chainTxs.map(tx => ({ ...tx, chain })));
        }

        return txs.sort((a, b) => b.timestamp - a.timestamp).slice(0, limit);
    }
}
```

Track and analyze crypto wallets across multiple blockchain networks.