# Gas Fee Optimizer

Optimize Ethereum transaction gas fees through strategic timing, routing alternatives, and Layer 2 solutions.

## Installation

```bash
/plugin install gas-fee-optimizer@claude-code-plugins-plus
```

## Usage

### Optimize Gas Command

```bash
/optimize-gas
```

Or use the shortcut:
```bash
/gas
```

### Example Queries

```bash
# Check current gas prices
/gas What's the current gas price on Ethereum?

# Timing optimization
/gas Should I mint this NFT now or wait for lower gas?

# Compare networks
/gas Compare gas costs: Ethereum mainnet vs Arbitrum vs Polygon

# Transaction-specific advice
/gas I need to swap 1 ETH for USDC - what's the best strategy?

# Historical analysis
/gas When is the best time of day to make transactions?
```

## Features

- **Real-Time Gas Analysis** - Current base fee and priority recommendations
- **Historical Context** - Compare to 24h and 7-day averages
- **Timing Optimization** - Best time windows for low-fee transactions
- **L2 Comparisons** - Gas costs across Arbitrum, Optimism, Base, zkSync
- **Sidechain Options** - Polygon, Gnosis Chain alternatives
- **Cost Estimates** - Transaction-specific cost calculations
- **Strategic Recommendations** - Wait vs execute now analysis

## What It Analyzes

1. **Current Network State** - Base fee, congestion level
2. **Historical Patterns** - Typical low-fee periods
3. **Transaction Type** - Gas estimates for different operations
4. **Alternative Routes** - L2 and sidechain comparison
5. **Urgency Factor** - Time-sensitive vs routine transactions
6. **Cost-Benefit** - Savings from waiting vs opportunity cost

## Output Includes

- Current gas price breakdown (base + priority fee)
- Estimated costs for common transaction types
- Historical comparison (percentile ranking)
- Best time windows for transactions
- L2/sidechain cost comparison table
- Specific optimization strategies
- Wait vs execute recommendation

## Transaction Types Covered

- **Simple Transfers** - ETH sends (~21,000 gas)
- **Token Transfers** - ERC-20 operations (~65,000 gas)
- **DEX Swaps** - Uniswap, SushiSwap (~150,000 gas)
- **NFT Mints** - Collection minting (~200,000 gas)
- **DeFi Operations** - Lending, staking, yield farming (varies)

## Layer 2 Networks Compared

- **Arbitrum** - Optimistic rollup, high liquidity
- **Optimism** - Optimistic rollup, EVM-equivalent
- **Base** - Coinbase L2, fast finality
- **zkSync** - Zero-knowledge rollup, high security
- **Polygon** - Sidechain, lowest cost
- **Gnosis Chain** - xDai sidechain

## Optimization Strategies

### Timing
- Identify low-congestion time windows
- Historical pattern analysis
- Weekend vs weekday comparison

### Routing
- L2 migration for frequent users
- Sidechain alternatives for specific use cases
- Bridge cost calculations

### Technical
- Batch transaction recommendations
- Gas-efficient contract interactions
- Approval optimization

## Data Sources

Analysis references:
- Etherscan Gas Tracker
- ETH Gas Station
- Blocknative (mempool data)
- L2Fees.info
- Gas Now

## Important Notes

- Gas prices are highly volatile and unpredictable
- Historical patterns don't guarantee future prices
- Consider transaction urgency and value
- Bridge costs may negate L2 savings for one-time transactions
- Opportunity cost of waiting may exceed gas savings
- This is optimization guidance, not financial advice

## Requirements

- Transaction type or operation description
- (Optional) Urgency level
- (Optional) Transaction value for cost-benefit analysis

## Files

- `commands/optimize-gas.md` - Main gas optimization command

## License

MIT License - See LICENSE file for details
