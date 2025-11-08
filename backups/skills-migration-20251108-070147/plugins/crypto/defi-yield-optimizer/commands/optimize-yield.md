---
description: Find and optimize DeFi yield farming opportunities across multiple protocols
shortcut: oy
---

# Optimize DeFi Yield

Comprehensive DeFi yield optimization across protocols with APY tracking, risk assessment, and automated strategy recommendations.

## Usage

When optimizing DeFi yield, implement comprehensive analysis across protocols:

### Required Parameters
- **Capital**: Amount to deploy
- **Risk Tolerance**: low, medium, high
- **Chains**: ethereum, bsc, polygon, arbitrum, all
- **Duration**: Days to farm (7, 30, 90, 365)
- **Strategy**: stable, balanced, aggressive

## Implementation

### 1. DeFi Yield Optimizer

```javascript
class DeFiYieldOptimizer {
    constructor() {
        this.protocols = {
            ethereum: {
                aave: { api: 'https://api.aave.com/v3', type: 'lending' },
                compound: { api: 'https://api.compound.finance/v3', type: 'lending' },
                uniswap: { api: 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', type: 'dex' },
                curve: { api: 'https://api.curve.fi', type: 'stableswap' },
                yearn: { api: 'https://api.yearn.finance/v1', type: 'aggregator' },
                convex: { api: 'https://api.convexfinance.com', type: 'boost' }
            },
            bsc: {
                pancakeswap: { api: 'https://api.pancakeswap.info/api/v2', type: 'dex' },
                venus: { api: 'https://api.venus.io', type: 'lending' },
                alpaca: { api: 'https://api.alpacafinance.org', type: 'leveraged' }
            },
            polygon: {
                quickswap: { api: 'https://api.quickswap.exchange', type: 'dex' },
                aavePolygon: { api: 'https://api.aave.com/polygon', type: 'lending' },
                balancer: { api: 'https://api.balancer.fi', type: 'dex' }
            }
        };

        this.riskScores = {
            stablecoin: 1,
            bluechip: 3,
            altcoin: 5,
            newProtocol: 8,
            leveraged: 9
        };
    }

    async optimizeYield(params) {
        const {
            capital = 10000,
            riskTolerance = 'medium',
            chains = ['ethereum', 'polygon'],
            duration = 30,
            strategy = 'balanced'
        } = params;

        // Fetch all opportunities
        const opportunities = await this.fetchAllOpportunities(chains);

        // Calculate risk-adjusted returns
        const analyzed = await this.analyzeOpportunities(opportunities, {
            capital,
            duration,
            riskTolerance
        });

        // Optimize portfolio allocation
        const optimized = await this.optimizePortfolio(analyzed, {
            strategy,
            capital,
            riskTolerance
        });

        // Generate recommendations
        const recommendations = this.generateRecommendations(optimized);

        return {
            timestamp: Date.now(),
            parameters: params,
            opportunities: analyzed.slice(0, 20),
            portfolio: optimized,
            recommendations,
            projections: await this.calculateProjections(optimized, duration),
            risks: await this.assessRisks(optimized)
        };
    }

    async fetchAllOpportunities(chains) {
        const opportunities = [];

        for (const chain of chains) {
            const protocols = this.protocols[chain];

            for (const [name, config] of Object.entries(protocols)) {
                try {
                    const data = await this.fetchProtocolData(name, config, chain);
                    opportunities.push(...data);
                } catch (error) {
                    console.error(`Failed to fetch ${name} on ${chain}:`, error);
                }
            }
        }

        return opportunities;
    }

    async fetchProtocolData(protocol, config, chain) {
        const opportunities = [];

        switch (config.type) {
            case 'lending':
                opportunities.push(...await this.fetchLendingOpportunities(protocol, chain));
                break;
            case 'dex':
                opportunities.push(...await this.fetchLiquidityPools(protocol, chain));
                break;
            case 'stableswap':
                opportunities.push(...await this.fetchStablePools(protocol, chain));
                break;
            case 'aggregator':
                opportunities.push(...await this.fetchVaults(protocol, chain));
                break;
            case 'leveraged':
                opportunities.push(...await this.fetchLeveragedFarms(protocol, chain));
                break;
        }

        return opportunities;
    }

    async fetchLendingOpportunities(protocol, chain) {
        // Simulate API call
        const markets = await this.mockFetchMarkets(protocol);

        return markets.map(market => ({
            protocol,
            chain,
            type: 'LENDING',
            asset: market.asset,
            apy: market.supplyAPY,
            apyBase: market.supplyAPY,
            apyReward: market.rewardAPY || 0,
            tvl: market.totalSupply * market.price,
            utilization: market.utilization,
            risk: this.calculateRisk(market),
            requirements: {
                minAmount: 0,
                lockPeriod: 0,
                gas: this.estimateGas('lending', chain)
            }
        }));
    }

    async fetchLiquidityPools(protocol, chain) {
        // Simulate fetching LP opportunities
        const pools = await this.mockFetchPools(protocol);

        return pools.map(pool => ({
            protocol,
            chain,
            type: 'LIQUIDITY',
            pair: `${pool.token0}/${pool.token1}`,
            apy: pool.apy,
            apyBase: pool.fees24h * 365 / pool.tvl * 100,
            apyReward: pool.rewardAPY || 0,
            tvl: pool.tvl,
            volume24h: pool.volume24h,
            impermanentLoss: this.estimateImpermanentLoss(pool),
            risk: this.calculatePoolRisk(pool),
            requirements: {
                minAmount: 100,
                lockPeriod: 0,
                gas: this.estimateGas('liquidity', chain)
            }
        }));
    }

    async fetchVaults(protocol, chain) {
        // Simulate vault strategies
        const vaults = await this.mockFetchVaults(protocol);

        return vaults.map(vault => ({
            protocol,
            chain,
            type: 'VAULT',
            name: vault.name,
            strategy: vault.strategy,
            apy: vault.apy,
            apyBase: vault.netAPY,
            apyReward: 0,
            tvl: vault.tvl,
            performanceFee: vault.performanceFee,
            managementFee: vault.managementFee,
            risk: this.calculateVaultRisk(vault),
            requirements: {
                minAmount: vault.minDeposit,
                lockPeriod: vault.lockPeriod || 0,
                gas: this.estimateGas('vault', chain)
            }
        }));
    }

    async analyzeOpportunities(opportunities, params) {
        const analyzed = [];

        for (const opp of opportunities) {
            const analysis = {
                ...opp,
                netAPY: this.calculateNetAPY(opp, params),
                riskScore: this.calculateRiskScore(opp),
                capitalEfficiency: this.calculateCapitalEfficiency(opp, params.capital),
                expectedReturn: this.calculateExpectedReturn(opp, params),
                breakeven: this.calculateBreakeven(opp, params),
                score: 0
            };

            // Calculate composite score
            analysis.score = this.calculateOpportunityScore(analysis, params);

            // Filter by risk tolerance
            if (this.meetsRiskTolerance(analysis, params.riskTolerance)) {
                analyzed.push(analysis);
            }
        }

        return analyzed.sort((a, b) => b.score - a.score);
    }

    calculateNetAPY(opp, params) {
        let netAPY = opp.apy;

        // Subtract fees
        if (opp.performanceFee) {
            netAPY *= (1 - opp.performanceFee / 100);
        }
        if (opp.managementFee) {
            netAPY -= opp.managementFee;
        }

        // Account for gas costs
        const gasPerYear = (365 / params.duration) * opp.requirements.gas;
        const gasImpact = (gasPerYear / params.capital) * 100;
        netAPY -= gasImpact;

        return Math.max(0, netAPY);
    }

    calculateRiskScore(opp) {
        let score = 5; // Base risk

        // Protocol risk
        const protocolAge = this.getProtocolAge(opp.protocol);
        if (protocolAge < 90) score += 3;
        else if (protocolAge < 365) score += 1;

        // TVL risk
        if (opp.tvl < 1000000) score += 3;
        else if (opp.tvl < 10000000) score += 2;
        else if (opp.tvl < 100000000) score += 1;

        // Type risk
        const typeRisks = {
            LENDING: 2,
            LIQUIDITY: 4,
            VAULT: 3,
            LEVERAGED: 8
        };
        score += typeRisks[opp.type] || 5;

        // Impermanent loss risk
        if (opp.impermanentLoss) {
            score += Math.min(5, opp.impermanentLoss);
        }

        return Math.min(10, score);
    }

    calculateOpportunityScore(analysis, params) {
        const weights = {
            low: { return: 0.3, risk: 0.5, efficiency: 0.2 },
            medium: { return: 0.5, risk: 0.3, efficiency: 0.2 },
            high: { return: 0.7, risk: 0.1, efficiency: 0.2 }
        };

        const w = weights[params.riskTolerance];

        const returnScore = Math.min(100, analysis.netAPY);
        const riskScore = 100 - (analysis.riskScore * 10);
        const efficiencyScore = analysis.capitalEfficiency * 100;

        return (returnScore * w.return) +
               (riskScore * w.risk) +
               (efficiencyScore * w.efficiency);
    }

    async optimizePortfolio(opportunities, params) {
        const portfolio = {
            allocations: [],
            totalAPY: 0,
            totalRisk: 0,
            totalAllocated: 0,
            diversification: 0
        };

        // Strategy-based allocation
        const strategies = {
            stable: this.stableStrategy,
            balanced: this.balancedStrategy,
            aggressive: this.aggressiveStrategy
        };

        const allocate = strategies[params.strategy].bind(this);
        portfolio.allocations = allocate(opportunities, params);

        // Calculate portfolio metrics
        for (const alloc of portfolio.allocations) {
            portfolio.totalAPY += alloc.apy * alloc.percentage / 100;
            portfolio.totalRisk += alloc.riskScore * alloc.percentage / 100;
            portfolio.totalAllocated += alloc.amount;
        }

        portfolio.diversification = this.calculateDiversification(portfolio.allocations);

        return portfolio;
    }

    stableStrategy(opportunities, params) {
        const allocations = [];
        let remainingCapital = params.capital;

        // Focus on low-risk opportunities
        const stableOpps = opportunities
            .filter(o => o.riskScore <= 3)
            .slice(0, 5);

        for (const opp of stableOpps) {
            const allocation = Math.min(
                remainingCapital * 0.3,
                remainingCapital
            );

            if (allocation > opp.requirements.minAmount) {
                allocations.push({
                    ...opp,
                    amount: allocation,
                    percentage: (allocation / params.capital) * 100
                });
                remainingCapital -= allocation;
            }
        }

        return allocations;
    }

    balancedStrategy(opportunities, params) {
        const allocations = [];
        let remainingCapital = params.capital;

        // Diversify across risk levels
        const buckets = {
            low: opportunities.filter(o => o.riskScore <= 3).slice(0, 2),
            medium: opportunities.filter(o => o.riskScore > 3 && o.riskScore <= 6).slice(0, 2),
            high: opportunities.filter(o => o.riskScore > 6).slice(0, 1)
        };

        const allocations_pct = { low: 0.5, medium: 0.35, high: 0.15 };

        for (const [risk, opps] of Object.entries(buckets)) {
            const bucketCapital = params.capital * allocations_pct[risk];
            const perOpp = bucketCapital / opps.length;

            for (const opp of opps) {
                if (perOpp > opp.requirements.minAmount) {
                    allocations.push({
                        ...opp,
                        amount: perOpp,
                        percentage: (perOpp / params.capital) * 100
                    });
                }
            }
        }

        return allocations;
    }

    aggressiveStrategy(opportunities, params) {
        const allocations = [];

        // Focus on highest returns regardless of risk
        const topOpps = opportunities
            .sort((a, b) => b.netAPY - a.netAPY)
            .slice(0, 3);

        const weights = [0.5, 0.3, 0.2];

        topOpps.forEach((opp, i) => {
            const amount = params.capital * weights[i];
            if (amount > opp.requirements.minAmount) {
                allocations.push({
                    ...opp,
                    amount,
                    percentage: weights[i] * 100
                });
            }
        });

        return allocations;
    }

    calculateProjections(portfolio, duration) {
        const daily = portfolio.totalAPY / 365;
        const projections = {
            daily: (portfolio.totalAllocated * daily / 100),
            weekly: (portfolio.totalAllocated * daily * 7 / 100),
            monthly: (portfolio.totalAllocated * daily * 30 / 100),
            total: (portfolio.totalAllocated * daily * duration / 100),
            finalValue: portfolio.totalAllocated * (1 + daily * duration / 100)
        };

        return projections;
    }

    assessRisks(portfolio) {
        return {
            protocolRisk: this.assessProtocolRisk(portfolio),
            smartContractRisk: this.assessSmartContractRisk(portfolio),
            impermanentLoss: this.assessImpermanentLoss(portfolio),
            liquidityRisk: this.assessLiquidityRisk(portfolio),
            composabilityRisk: this.assessComposabilityRisk(portfolio),
            overall: portfolio.totalRisk
        };
    }

    assessProtocolRisk(portfolio) {
        const risks = [];

        for (const alloc of portfolio.allocations) {
            if (this.getProtocolAge(alloc.protocol) < 180) {
                risks.push({
                    protocol: alloc.protocol,
                    risk: 'NEW_PROTOCOL',
                    severity: 'MEDIUM'
                });
            }

            if (alloc.tvl < 10000000) {
                risks.push({
                    protocol: alloc.protocol,
                    risk: 'LOW_TVL',
                    severity: 'LOW'
                });
            }
        }

        return risks;
    }

    estimateImpermanentLoss(pool) {
        // Simplified IL calculation
        const priceRatio = pool.token0Price / pool.token1Price;
        const priceChange = Math.abs(1 - priceRatio);

        if (priceChange < 0.1) return 0.5;
        if (priceChange < 0.25) return 1.5;
        if (priceChange < 0.5) return 3.5;
        if (priceChange < 1) return 5.5;
        return 8;
    }
}
```

### 2. Display Interface

```javascript
class YieldDisplay {
    displayOptimization(result) {
        return `
╔════════════════════════════════════════════════════════════════╗
║                   DEFI YIELD OPTIMIZATION                      ║
╠════════════════════════════════════════════════════════════════╣
║ Capital:       $${result.parameters.capital.toLocaleString().padEnd(47)} ║
║ Strategy:      ${result.parameters.strategy.padEnd(48)} ║
║ Duration:      ${(result.parameters.duration + ' days').padEnd(48)} ║
║ Risk Level:    ${result.parameters.riskTolerance.padEnd(48)} ║
╠════════════════════════════════════════════════════════════════╣
║                    TOP OPPORTUNITIES                           ║
╠════════════════════════════════════════════════════════════════╣
${this.formatOpportunities(result.opportunities.slice(0, 5))}
╠════════════════════════════════════════════════════════════════╣
║                  OPTIMIZED PORTFOLIO                           ║
╠════════════════════════════════════════════════════════════════╣
${this.formatPortfolio(result.portfolio)}
╠════════════════════════════════════════════════════════════════╣
║                    PROJECTIONS                                 ║
╠════════════════════════════════════════════════════════════════╣
║ Daily Yield:   $${result.projections.daily.toFixed(2).padEnd(47)} ║
║ Weekly Yield:  $${result.projections.weekly.toFixed(2).padEnd(47)} ║
║ Monthly Yield: $${result.projections.monthly.toFixed(2).padEnd(47)} ║
║ Total Return:  $${result.projections.total.toFixed(2).padEnd(47)} ║
║ Final Value:   $${result.projections.finalValue.toFixed(2).padEnd(47)} ║
╠════════════════════════════════════════════════════════════════╣
║                      RISKS                                     ║
╠════════════════════════════════════════════════════════════════╣
${this.formatRisks(result.risks)}
╚════════════════════════════════════════════════════════════════╝
`;
    }

    formatOpportunities(opportunities) {
        const lines = [];

        for (const opp of opportunities) {
            const apyStr = `${opp.apy.toFixed(2)}%`;
            const tvlStr = this.formatTVL(opp.tvl);
            const riskStr = this.getRiskEmoji(opp.riskScore);

            lines.push(
                `║ ${opp.protocol.padEnd(12)} ${opp.type.padEnd(10)} ` +
                `${apyStr.padEnd(8)} TVL: ${tvlStr.padEnd(10)} ${riskStr} ║`
            );
        }

        return lines.join('\n');
    }

    formatPortfolio(portfolio) {
        const lines = [];

        lines.push(`║ Total APY:     ${portfolio.totalAPY.toFixed(2)}%                                     ║`);
        lines.push(`║ Risk Score:    ${portfolio.totalRisk.toFixed(1)}/10                                     ║`);
        lines.push(`║ Diversification: ${this.getDiversificationLabel(portfolio.diversification)}                   ║`);
        lines.push(`║                                                                ║`);

        for (const alloc of portfolio.allocations.slice(0, 3)) {
            lines.push(
                `║ • ${alloc.protocol.padEnd(10)} $${alloc.amount.toFixed(0).padEnd(8)} ` +
                `(${alloc.percentage.toFixed(1)}%) APY: ${alloc.apy.toFixed(2)}%         ║`
            );
        }

        return lines.join('\n');
    }

    formatRisks(risks) {
        const riskLevels = {
            protocolRisk: risks.protocolRisk.length > 0 ? 'PRESENT' : 'LOW',
            smartContractRisk: risks.smartContractRisk || 'MEDIUM',
            impermanentLoss: risks.impermanentLoss || 'MODERATE',
            liquidityRisk: risks.liquidityRisk || 'LOW'
        };

        const lines = [];
        for (const [type, level] of Object.entries(riskLevels)) {
            const emoji = this.getRiskLevelEmoji(level);
            lines.push(`║ ${type.padEnd(20)} ${emoji} ${level.padEnd(25)} ║`);
        }

        return lines.join('\n');
    }

    formatTVL(tvl) {
        if (tvl > 1e9) return `$${(tvl / 1e9).toFixed(2)}B`;
        if (tvl > 1e6) return `$${(tvl / 1e6).toFixed(2)}M`;
        if (tvl > 1e3) return `$${(tvl / 1e3).toFixed(2)}K`;
        return `$${tvl.toFixed(0)}`;
    }

    getRiskEmoji(score) {
        if (score <= 2) return '';
        if (score <= 5) return '';
        if (score <= 7) return '';
        return '';
    }

    getDiversificationLabel(score) {
        if (score > 0.8) return 'EXCELLENT';
        if (score > 0.6) return 'GOOD';
        if (score > 0.4) return 'MODERATE';
        return 'LOW';
    }

    getRiskLevelEmoji(level) {
        const emojis = {
            LOW: '',
            MODERATE: '️',
            MEDIUM: '️',
            HIGH: '',
            PRESENT: '️'
        };
        return emojis[level] || '';
    }
}
```

### 3. Auto-Compound Calculator

```javascript
class AutoCompoundCalculator {
    calculateOptimalFrequency(params) {
        const {
            principal,
            apy,
            gasCost,
            duration
        } = params;

        const frequencies = [1, 7, 14, 30, 90, 365];
        const results = [];

        for (const freq of frequencies) {
            const compoundsPerYear = 365 / freq;
            const gasPerYear = compoundsPerYear * gasCost;
            const apr = apy / 100;

            // Calculate compound interest with gas costs
            const finalValue = principal * Math.pow(1 + apr / compoundsPerYear, compoundsPerYear * duration / 365) - gasPerYear;
            const netReturn = finalValue - principal;
            const netAPY = (netReturn / principal) * (365 / duration) * 100;

            results.push({
                frequency: freq,
                compounds: Math.floor(duration / freq),
                gasCost: gasPerYear * duration / 365,
                finalValue,
                netAPY,
                profit: netReturn
            });
        }

        return results.sort((a, b) => b.netAPY - a.netAPY)[0];
    }
}
```

## Error Handling

```javascript
try {
    const optimizer = new DeFiYieldOptimizer();
    const result = await optimizer.optimizeYield({
        capital: 10000,
        riskTolerance: 'medium',
        chains: ['ethereum', 'polygon'],
        duration: 30,
        strategy: 'balanced'
    });

    const display = new YieldDisplay();
    console.log(display.displayOptimization(result));

} catch (error) {
    console.error('Yield optimization failed:', error);
}
```

This command provides comprehensive DeFi yield optimization with risk assessment and portfolio allocation strategies.