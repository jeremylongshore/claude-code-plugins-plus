# Staking Rewards Optimizer

Optimize staking rewards across multiple protocols and blockchains to maximize yield while managing risk.

## Installation

```bash
/plugin install staking-rewards-optimizer@claude-code-plugins-plus
```

## Usage

### Optimize Staking Command

```bash
/optimize-staking
```

Or use the shortcut:
```bash
/stake
```

### Example Queries

```bash
# Get current best staking opportunities
/stake What are the best staking opportunities for ETH?

# Optimize existing portfolio
/stake Optimize my portfolio: 50 ATOM at 19% APY, 100 DOT at 14% APY, 5 ETH at 4% APY

# Compare liquid staking options
/stake Compare liquid staking: Lido vs Rocket Pool vs Frax

# Find opportunities for specific amount
/stake I have $10,000 to stake - what's the optimal allocation?
```

## Features

- **Multi-Chain Analysis** - Compare opportunities across Ethereum, Cosmos, Polkadot, Solana, and more
- **Risk Assessment** - Evaluate smart contract risks, validator risks, and lock-up constraints
- **Yield Optimization** - Calculate optimal allocation strategies for maximum returns
- **Liquid Staking** - Compare liquid staking derivatives and their benefits
- **Cost Analysis** - Factor in gas fees, bridging costs, and opportunity costs
- **Compounding Strategies** - Identify auto-compound and restaking opportunities

## What It Analyzes

1. **Current Positions** - Review your existing staking allocations
2. **Market Opportunities** - Scan yields across major protocols
3. **Risk vs Reward** - Balance higher yields with safety considerations
4. **Implementation Costs** - Calculate fees and transaction costs
5. **Expected Returns** - Project improvement in annual yields

## Output Includes

- Comparative table of staking opportunities
- Recommended allocation percentages
- Risk assessment for each protocol
- Step-by-step implementation plan
- Expected ROI improvement
- Important warnings and considerations

## Important Notes

- APYs are variable and change frequently
- Historical yields don't guarantee future returns
- Consider your own risk tolerance and liquidity needs
- This provides educational information, not financial advice
- Always DYOR (Do Your Own Research) before staking

## Data Sources

Recommendations reference data from:
- DefiLlama
- StakingRewards.com
- Protocol documentation
- Validator performance metrics

## Requirements

- Understanding of staking concepts
- Knowledge of your risk tolerance
- Access to supported wallets for implementation

## Files

- `commands/optimize-staking.md` - Main staking optimization command

## License

MIT License - See LICENSE file for details
