# Usage Examples

## View Pending Transactions

### Basic View

```bash
python mempool_analyzer.py pending
```

### Limit Results

```bash
python mempool_analyzer.py pending --limit 20
```

### JSON Output

```bash
python mempool_analyzer.py pending --format json
```

## Gas Price Analysis

### Current Gas Prices

```bash
python mempool_analyzer.py gas
```

### Gas Recommendations

```bash
python mempool_analyzer.py gas
# Output shows:
# - Current base fee
# - Gas price distribution (10th, 25th, 50th, 75th, 90th percentile)
# - Recommendations for slow, standard, fast, instant
```

### JSON for Programmatic Use

```bash
python mempool_analyzer.py gas --format json
```

## Pending DEX Swaps

### View All Pending Swaps

```bash
python mempool_analyzer.py swaps
```

### Analyze More Transactions

```bash
python mempool_analyzer.py swaps --limit 200
```

## MEV Opportunity Scanning

### Scan for Opportunities

```bash
python mempool_analyzer.py mev
```

### Detailed Analysis

```bash
python mempool_analyzer.py mev --limit 300 -v
```

### JSON Output

```bash
python mempool_analyzer.py mev --format json
```

## Mempool Summary

### Quick Overview

```bash
python mempool_analyzer.py summary
```

## Watch Specific Contract

### Monitor Uniswap Router

```bash
python mempool_analyzer.py watch 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
```

### Monitor Any Contract

```bash
python mempool_analyzer.py watch 0xYOUR_CONTRACT_ADDRESS --limit 200
```

## Connection Status

### Check RPC Connection

```bash
python mempool_analyzer.py status
```

## Different Chains

### Polygon

```bash
python mempool_analyzer.py --chain polygon pending
python mempool_analyzer.py --chain polygon gas
```

### Arbitrum

```bash
python mempool_analyzer.py --chain arbitrum summary
```

### Custom RPC URL

```bash
python mempool_analyzer.py --rpc-url https://your-rpc.example.com pending
```

## Common Workflows

### Pre-Transaction Gas Check

```bash
# Before sending a transaction, check optimal gas
python mempool_analyzer.py gas

# Use "Fast" recommendation for quick confirmation
# Use "Standard" for normal priority
# Use "Slow" if not time-sensitive
```

### Monitor for Front-Running Risk

```bash
# Check if there are pending swaps that might affect your trade
python mempool_analyzer.py swaps

# High-value pending swaps = potential slippage
```

### MEV Opportunity Research

```bash
# Educational: See what MEV opportunities exist
python mempool_analyzer.py mev -v

# Note: This is for research/education only
# Real MEV extraction requires specialized infrastructure
```

## Programmatic Usage

```python
from rpc_client import RPCClient
from gas_analyzer import GasAnalyzer
from mev_detector import MEVDetector

# Initialize
client = RPCClient()
gas_analyzer = GasAnalyzer()
mev_detector = MEVDetector()

# Get pending transactions
pending = client.get_pending_transactions(limit=100)

# Analyze gas
gas_info = client.get_gas_price()
distribution = gas_analyzer.analyze_pending_gas(pending)

print(f"Median gas: {distribution.median_gwei:.1f} gwei")

# Detect swaps
swaps = mev_detector.detect_pending_swaps(pending)
print(f"Pending swaps: {len(swaps)}")
```

## Integration with jq

### Filter High Gas Transactions

```bash
python mempool_analyzer.py pending --format json | \
  jq '[.[] | select(.gas_price > 50000000000)]'
```

### Count by Transaction Type

```bash
python mempool_analyzer.py swaps --format json | \
  jq 'group_by(.dex) | map({dex: .[0].dex, count: length})'
```

### Export Gas Data

```bash
python mempool_analyzer.py gas --format json > gas_snapshot.json
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
