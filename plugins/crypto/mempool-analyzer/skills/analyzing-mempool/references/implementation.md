# Implementation Details

## Gas Price Distribution Analysis

The gas analysis command calculates percentile-based recommendations from pending transactions:

**Gas Recommendations:**
- Slow (10th percentile): May take 10+ blocks
- Standard (50th percentile): 2-5 blocks
- Fast (75th percentile): 1-2 blocks
- Instant (90th percentile): Next block likely

## MEV Detection Details

MEV detection scans for common patterns:
- **Sandwich attacks**: Detects front-run + back-run pairs targeting the same swap
- **Arbitrage**: Identifies circular token paths (A→B→A) across DEXs
- **Liquidation**: Finds health-factor monitoring and repay+seize patterns

**Important:** MEV detection is for educational purposes only. Real MEV extraction requires:
- Specialized block-builder infrastructure (Flashbots, MEV-Boost)
- Sub-millisecond execution timing
- Significant capital for gas auctions

## DEX Swap Detection

The `swaps` command identifies pending DEX transactions by matching method selectors:
- Uniswap V2/V3: `swapExactTokensForTokens`, `exactInputSingle`
- SushiSwap: Same interface as Uniswap V2
- 1inch: `swap`, `unoswap` aggregation methods

## Multi-Chain Support

Supported chains and their mempool characteristics:
| Chain | Mempool Access | Block Time | Notes |
|-------|---------------|------------|-------|
| Ethereum | Full | ~12s | Richest MEV environment |
| Polygon | Full | ~2s | Lower gas, faster blocks |
| Arbitrum | Limited | ~0.25s | Sequencer-based, less MEV |
| Optimism | Limited | ~2s | Sequencer-based |
| Base | Limited | ~2s | Coinbase sequencer |

## Contract Watching

The `watch` command monitors pending transactions to a specific contract address:
1. Filters mempool by `to` address
2. Decodes known method selectors
3. Estimates gas cost in USD
4. Identifies transaction type (swap, approve, transfer, etc.)

## Configuration

Edit `${CLAUDE_SKILL_DIR}/config/settings.yaml`:
```yaml
rpc_endpoints:
  ethereum: "https://rpc.ankr.com/eth"
  polygon: "https://rpc.ankr.com/polygon"
  arbitrum: "https://rpc.ankr.com/arbitrum"

defaults:
  chain: ethereum
  limit: 50
  output_format: table
```
