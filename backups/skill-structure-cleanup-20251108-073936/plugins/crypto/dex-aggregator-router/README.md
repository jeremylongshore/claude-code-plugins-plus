# DEX Aggregator Router

Find optimal routing for token swaps across multiple decentralized exchanges to maximize output and minimize costs.

## Installation

```bash
/plugin install dex-aggregator-router@claude-code-plugins-plus
```

## Usage

### Find Best Route Command

```bash
/find-best-route
```

Or use the shortcut:
```bash
/route
```

### Example Queries

```bash
# Simple swap routing
/route Best route to swap 10 ETH for USDC

# Compare exchanges
/route Compare Uniswap vs SushiSwap for DAI to USDC

# Large trade optimization
/route I want to swap $50,000 USDT to ETH - optimize routing

# Why aggregators differ
/route Why does 1inch show better rate than Uniswap?

# Multi-hop analysis
/route Should I swap LINK → ETH → USDC or LINK → USDC directly?
```

## Features

- **Multi-DEX Comparison** - Analyze routes across Uniswap, SushiSwap, Curve, Balancer
- **Route Discovery** - Find direct, multi-hop, and split order paths
- **Price Impact Analysis** - Calculate slippage for different trade sizes
- **Gas Cost Optimization** - Factor in transaction costs vs savings
- **Aggregator Integration** - Leverage 1inch, Paraswap, Matcha routing
- **Execution Parameters** - Optimal slippage and deadline settings
- **MEV Protection** - Recommendations for large trade protection

## What It Analyzes

1. **Direct Routes** - Single DEX, single hop swaps
2. **Multi-Hop Paths** - Routes through intermediate tokens
3. **Split Orders** - Partial routing across multiple DEXs
4. **Price Impact** - Slippage based on trade size
5. **Gas Costs** - Transaction fees for each route option
6. **Net Output** - Total received after all costs
7. **Liquidity Depth** - Pool sizes and available liquidity

## Output Includes

- Recommended best route with detailed path
- Comparison table of top 3-5 routes
- Price impact calculations
- Gas cost estimates
- Slippage tolerance recommendations
- Execution parameters
- Risk factors and considerations
- Alternative strategies for large trades

## Supported DEXs

### Ethereum Mainnet
- **Uniswap V2/V3** - Most liquid, standard pairs
- **SushiSwap** - Alternative with good liquidity
- **Curve** - Best for stablecoins
- **Balancer** - Multi-token pools
- **1inch** - Meta-aggregator
- **Paraswap** - Smart routing
- **CoW Swap** - MEV-protected batch auctions

### Layer 2s
- Arbitrum, Optimism, Base, Polygon support
- Network-specific liquidity considerations

## Trade Size Recommendations

### Small Trades (< $1,000)
- Prioritize low gas costs
- Use simple direct routes
- Uniswap V2 often best

### Medium Trades ($1,000 - $10,000)
- Balance price impact and gas
- Consider multi-hop if beneficial
- Aggregators provide value

### Large Trades ($10,000 - $100,000)
- Split routing often optimal
- Use MEV protection
- Higher slippage tolerance needed

### Whale Trades (> $100,000)
- Consider OTC desks
- TWAP (time-weighted) execution
- Professional market makers

## Key Metrics Explained

### Price Impact
Percentage difference between expected and execution price due to trade size affecting pool balance.

### Slippage Tolerance
Maximum acceptable price movement before transaction reverts.

### Effective Rate
Final exchange rate after all fees, impacts, and costs.

### Total Cost
Combined cost of price impact, DEX fees, and gas.

## Optimization Strategies

### Route Splitting
Divide trade across multiple DEXs to reduce per-pool impact.

### Multi-Hop Routing
Route through intermediate tokens when direct pairs have poor liquidity.

### Gas vs Impact Trade-off
Sometimes higher gas cost route has lower price impact, better for large trades.

## Important Notes

- Always verify token contract addresses (scams exist)
- Price impact is non-linear - doubles trade size ≠ doubles impact
- Gas estimates are approximate, actual costs may vary
- Slippage protection is essential in volatile markets
- MEV bots can frontrun large trades without protection
- Aggregators like 1inch already do this optimization
- This provides routing analysis, not financial advice

## Data Sources

Analysis references:
- DEX liquidity pools (on-chain data)
- 1inch API (aggregator routing)
- Paraswap API (comparative pricing)
- Gas price feeds (Etherscan, Blocknative)

## Requirements

- Token pair (from token, to token)
- Trade amount
- Network (Ethereum, Arbitrum, etc.)
- (Optional) Urgency and slippage tolerance

## Files

- `commands/find-best-route.md` - Main DEX routing command

## License

MIT License - See LICENSE file for details
