# DEX Aggregator Router Examples

Comprehensive usage examples for the DEX Aggregator Router.

## Quick Start

### Basic Quote

Get the best price across all aggregators:

```bash
python dex_router.py ETH USDC 1.0
```

Output:

```
Fetching quotes for 1.0 ETH → USDC...

Quote from 1inch
════════════════════════════════════════
Input:          1.0 ETH
Output:         2,543.22 USDC
Rate:           2,543.22 USDC/ETH
Price Impact:   0.05%
Gas Cost:       $11.25
Effective Rate: 2,531.97
Protocols:      Uniswap V3
```

### Specify Chain

Route on Arbitrum for lower gas:

```bash
python dex_router.py ETH USDC 1.0 --chain arbitrum
```

### JSON Output

Get machine-readable output:

```bash
python dex_router.py ETH USDC 1.0 --output json
```

```json
{
  "source": "1inch",
  "input_token": "ETH",
  "output_token": "USDC",
  "input_amount": 1.0,
  "output_amount": 2543.22,
  "price": 2543.22,
  "price_impact": 0.05,
  "gas_cost_usd": 11.25,
  "effective_rate": 2531.97,
  "protocols": ["Uniswap V3"]
}
```

---

## Compare Mode

### Compare All Aggregators

See prices from all sources:

```bash
python dex_router.py ETH USDC 5.0 --compare
```

Output:

```
DEX Route Comparison
══════════════════════════════════════════════════════════════════════
 Rank  Source      Output        Rate       Gas    Score    Savings
──────────────────────────────────────────────────────────────────────
 #1    1inch       12,716.10    2,543.22   $11.25   94      +0.15%
 #2    0x          12,705.00    2,541.00   $12.00   89      +0.06%
 #3    Paraswap    12,699.20    2,539.84   $13.50   85      +0.00%
──────────────────────────────────────────────────────────────────────

Spread: 0.15%
Recommendation: Best route saves 0.15%. Worth optimizing.

Medium trade: Compare routes and consider multi-hop if savings exceed 0.3%.
```

### CSV Export

Export comparison to spreadsheet:

```bash
python dex_router.py ETH USDC 5.0 --compare --output csv > comparison.csv
```

```csv
rank,source,output_amount,effective_rate,gas_cost_usd,score,savings_pct
1,1inch,12716.10,2543.22,11.25,94,0.15
2,0x,12705.00,2541.00,12.00,89,0.06
3,Paraswap,12699.20,2539.84,13.50,85,0.00
```

---

## Split Order Mode

### Analyze Large Trade Splitting

For trades >$10K, see optimal split:

```bash
python dex_router.py ETH USDC 50.0 --split
```

Output:

```
Split Order Recommendation
══════════════════════════════════════════════════════════════════════
 Venue       Allocation    Amount      Expected         Gas
──────────────────────────────────────────────────────────────────────
 1inch          55.0%      27.5 ETH    69,938.60       $11.25
 Paraswap       30.0%      15.0 ETH    38,097.60       $13.50
 0x             15.0%       7.5 ETH    19,057.50       $12.00
──────────────────────────────────────────────────────────────────────

Total Output:  127,093.70 USDC
Single Venue:  126,200.00 USDC
Improvement:   +0.71% ($893.70 extra)
Total Gas:     $36.75

Split order saves $856.95 (0.71% improvement after gas)
```

### Small Trade (No Split)

For small trades, split isn't recommended:

```bash
python dex_router.py ETH USDC 0.5 --split
```

Output:

```
Single venue is optimal for this trade size.
```

---

## MEV Risk Assessment

### Check MEV Exposure

Assess sandwich attack risk:

```bash
python dex_router.py ETH USDC 20.0 --mev-check
```

Output:

```
╭──────────────────── MEV Risk Level ────────────────────╮
│ MEDIUM (Score: 52/100)                                 │
╰────────────────────────────────────────────────────────╯

Estimated Exposure: $127.50

Risk Factors
══════════════════════════════════════════════════════════════════════
 Factor              Score    Weight    Description
──────────────────────────────────────────────────────────────────────
 Trade Size            60      35%      $50,000 trade attracts MEV searchers
 Price Impact          30      25%      0.45% impact creates arbitrage opportunity
 Route Complexity      40      15%      2 DEX(s) in route increases surface area
 Token Volatility      30      15%      Volatile tokens enable larger sandwich
 Liquidity Depth       50      10%      Lower liquidity increases MEV opportunity
──────────────────────────────────────────────────────────────────────

Protection Options:
  • MEV Blocker (85% effective)
    RPC endpoint that routes to multiple builders
  • Private Transaction (80% effective)
    Send directly to block builders
  • Slippage Tightening (50% effective)
    Set tight slippage tolerance to reject sandwich

Recommendation: MEDIUM MEV RISK: Consider using MEV Blocker or tight slippage.
                Estimated exposure: $127.50
```

### High-Value Trade MEV Check

```bash
python dex_router.py ETH USDC 100.0 --mev-check
```

Output includes stronger warnings and Flashbots recommendation.

---

## Full Analysis Mode

### Complete Trade Analysis

Run all analyses together:

```bash
python dex_router.py ETH USDC 25.0 --full
```

Output:

```
════════════════════════════════════════════════════════════════════════
COMPLETE DEX ANALYSIS
════════════════════════════════════════════════════════════════════════

--- ROUTE COMPARISON ---

[Full comparison table]

--- SPLIT ORDER ANALYSIS ---

[Split recommendations]

--- MEV RISK ASSESSMENT ---

[Risk assessment with protection options]
```

### Full Analysis to JSON File

```bash
python dex_router.py ETH USDC 25.0 --full --output json > analysis.json
```

---

## Advanced Usage

### Custom Gas Price

Override gas price estimate:

```bash
python dex_router.py ETH USDC 10.0 --gas-price 50
```

### Custom ETH Price

Use specific ETH price for calculations:

```bash
python dex_router.py ETH USDC 10.0 --eth-price 3000
```

### Different Token Pairs

```bash
# Stablecoin swap
python dex_router.py USDC DAI 10000

# BTC to ETH
python dex_router.py WBTC ETH 1.0

# Low-cap token (use address)
python dex_router.py ETH 0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984 5.0
```

### Disable Colors

For logging or piping:

```bash
python dex_router.py ETH USDC 1.0 --no-color
```

---

## Pipeline Examples

### Best Price Alert Script

```bash
#!/bin/bash
BEST_RATE=$(python dex_router.py ETH USDC 1.0 --output json | jq '.effective_rate')
echo "Current best rate: $BEST_RATE USDC/ETH"

if (( $(echo "$BEST_RATE > 2600" | bc -l) )); then
    echo "ALERT: Rate above 2600!"
fi
```

### Batch Comparison

```bash
for amount in 1 5 10 50 100; do
    echo "=== $amount ETH ==="
    python dex_router.py ETH USDC $amount --compare --no-color
done
```

### Log to File

```bash
python dex_router.py ETH USDC 10.0 --full --output json >> trades.jsonl
```

---

## Demo Mode

When APIs are unavailable, use demo mode:

```bash
python dex_router.py --demo
```

This shows example output without making API calls.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
