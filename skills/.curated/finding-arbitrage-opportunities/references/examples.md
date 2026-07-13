# Examples

Comprehensive usage examples for arbitrage opportunity detection.

---

## Example 1: Basic Spread Scan

Scan for ETH/USDC arbitrage across all enabled exchanges.

### Command

```bash
python arb_finder.py scan ETH USDC
```

### Output

```
======================== ARBITRAGE SCAN RESULTS ========================

Pair: ETH/USDC
Exchanges scanned: 9
Opportunities found: 3

----------------------------------------------------------------------
CURRENT PRICES
----------------------------------------------------------------------
Exchange        Bid             Ask         Spread
----------------------------------------------------------------------
Coinbase        $2,543.80       $2,544.10   0.012%
Uniswap V3      $2,543.50       $2,544.00   0.020%
Kraken          $2,542.30       $2,542.80   0.020%
Binance         $2,541.20       $2,541.50   0.012%
KuCoin          $2,541.00       $2,541.40   0.016%
OKX             $2,540.80       $2,541.20   0.016%
SushiSwap       $2,540.50       $2,541.00   0.020%
Curve           $2,540.20       $2,540.60   0.016%
Balancer        $2,539.80       $2,540.30   0.020%

----------------------------------------------------------------------
OPPORTUNITIES
----------------------------------------------------------------------
Buy On          Sell On         Gross    Net      Risk
----------------------------------------------------------------------
Balancer        Coinbase        +0.157%  +0.037%  🟢 LOW
Curve           Uniswap V3      +0.130%  +0.026%  🟡 MEDIUM
SushiSwap       Kraken          +0.071%  -0.029%  🟡 MEDIUM

----------------------------------------------------------------------
BEST OPPORTUNITY
----------------------------------------------------------------------
Buy on Balancer at $2,540.30
Sell on Coinbase at $2,543.80

Gross spread: +0.1378%
Buy fee: -0.10%
Sell fee: -0.60%
Gas cost: ~$11.25
----------------------------------------------------------------------
Net spread: +0.0368%
Risk: 🟢 LOW

Notes:
  • DEX-to-CEX trade requires bridging
  • Consider gas costs for DEX execution

✓ PROFITABLE - Consider execution
```

---

## Example 2: CEX-Only Scan

Scan only centralized exchanges (faster, no gas costs).

### Command

```bash
python arb_finder.py scan BTC USDT --cex-only --min-profit 0.05
```

### Output

```
======================== ARBITRAGE SCAN RESULTS ========================

Pair: BTC/USDT
Exchanges scanned: 5
Opportunities found: 1

----------------------------------------------------------------------
CURRENT PRICES
----------------------------------------------------------------------
Exchange        Bid             Ask         Spread
----------------------------------------------------------------------
Coinbase        $67,920.00      $67,950.00  0.044%
Binance         $67,850.00      $67,865.00  0.022%
Kraken          $67,830.00      $67,860.00  0.044%
KuCoin          $67,820.00      $67,850.00  0.044%
OKX             $67,810.00      $67,840.00  0.044%

----------------------------------------------------------------------
OPPORTUNITIES
----------------------------------------------------------------------
Buy On          Sell On         Gross    Net      Risk
----------------------------------------------------------------------
OKX             Coinbase        +0.118%  +0.052%  🟢 LOW

----------------------------------------------------------------------
BEST OPPORTUNITY
----------------------------------------------------------------------
Buy on OKX at $67,840.00
Sell on Coinbase at $67,920.00

Gross spread: +0.1179%
Buy fee: -0.10%
Sell fee: -0.60%
----------------------------------------------------------------------
Net spread: +0.0519%
Risk: 🟢 LOW

✓ PROFITABLE - Consider execution
```

---

## Example 3: Specific Exchange Comparison

Compare prices between specific exchanges only.

### Command

```bash
python arb_finder.py scan ETH USDC --exchanges binance,coinbase,kraken
```

### Output

```
======================== ARBITRAGE SCAN RESULTS ========================

Pair: ETH/USDC
Exchanges scanned: 3
Opportunities found: 1

----------------------------------------------------------------------
CURRENT PRICES
----------------------------------------------------------------------
Exchange        Bid             Ask         Spread
----------------------------------------------------------------------
Coinbase        $2,543.80       $2,544.10   0.012%
Kraken          $2,542.30       $2,542.80   0.020%
Binance         $2,541.20       $2,541.50   0.012%

----------------------------------------------------------------------
OPPORTUNITIES
----------------------------------------------------------------------
Buy On          Sell On         Gross    Net      Risk
----------------------------------------------------------------------
Binance         Coinbase        +0.091%  +0.021%  🟢 LOW

----------------------------------------------------------------------
BEST OPPORTUNITY
----------------------------------------------------------------------
Buy on Binance at $2,541.50
Sell on Coinbase at $2,543.80

Gross spread: +0.0905%
Buy fee: -0.10%
Sell fee: -0.60%
----------------------------------------------------------------------
Net spread: +0.0205%
Risk: 🟢 LOW

✓ PROFITABLE - Consider execution
```

---

## Example 4: Triangular Arbitrage Scan

Find triangular arbitrage paths on a single exchange.

### Command

```bash
python arb_finder.py triangular binance --min-profit 0.0
```

### Output

```
======================== TRIANGULAR ARBITRAGE ========================

Found 6 paths

Path                           Gross      Fees       Net
----------------------------------------------------------------------
ETH → BTC → USDT → ETH        +0.3520%   -0.3000%   +0.0520%
BNB → ETH → USDT → BNB        +0.2850%   -0.3000%   -0.0150%
BNB → BTC → USDT → BNB        +0.2410%   -0.3000%   -0.0590%
ETH → USDC → USDT → ETH       +0.1800%   -0.3000%   -0.1200%
BTC → USDC → USDT → BTC       +0.1500%   -0.3000%   -0.1500%
BNB → BTC → ETH → BNB         +0.1200%   -0.3000%   -0.1800%

----------------------------------------------------------------------
BEST PATH
----------------------------------------------------------------------
Path: ETH → BTC → USDT → ETH
Exchange: binance

Execution Steps:
  1. Sell ETH for BTC at 0.03745
  2. Sell BTC for USDT at 67850.00
  3. Buy ETH with USDT at 2541.50

Gross Profit: +0.3520%
Total Fees: -0.3000%
Net Profit: +0.0520%

✓ PROFITABLE - Consider execution
```

---

## Example 5: Real-Time Monitoring

Monitor for opportunities with alerts.

### Command

```bash
python arb_finder.py monitor ETH USDC --threshold 0.3 --interval 5
```

### Output

```
Monitoring ETH/USDC for spreads > 0.3%
Interval: 5s | Press Ctrl+C to stop

[1] Best: Binance → Coinbase (+0.021%) - below threshold
[2] Best: Binance → Coinbase (+0.019%) - below threshold
[3] Best: Binance → Coinbase (+0.025%) - below threshold

============================================================
🚨 ARBITRAGE ALERT
============================================================

ETH/USDC spread +0.342%
Buy on OKX at $2,535.20
Sell on Coinbase at $2,543.88

Risk: 🟢 LOW
============================================================

[5] Best: OKX → Coinbase (+0.342%) - ALERT TRIGGERED
[6] Best: OKX → Coinbase (+0.285%) - below threshold
^C
Monitoring stopped
```

---

## Example 6: Profit Calculation

Calculate exact profit for a specific trade.

### Command

```bash
python arb_finder.py calc \
  --buy-exchange binance \
  --sell-exchange coinbase \
  --pair ETH/USDC \
  --amount 10
```

### Output

```
======================== PROFIT BREAKDOWN ========================

Trade: 10 ETH
Buy on binance at $2,541.50
Sell on coinbase at $2,543.80

Gross Profit: $23.00 (+0.090%)

Costs:
  Buy fee:        -$2.54
  Sell fee:       -$15.26
  Withdrawal:     -$1.27
  Gas:            -$0.00
  Slippage:       -$2.54
  ------------------------------
  Total:          -$21.62

Net Profit: $1.38 (+0.005%)
Breakeven spread: 0.085%

✓ PROFITABLE
```

---

## Example 7: Manual Price Entry

Calculate with specific buy/sell prices.

### Command

```bash
python arb_finder.py calc \
  --buy-exchange binance \
  --sell-exchange coinbase \
  --pair ETH/USDC \
  --amount 50 \
  --buy-price 2500.00 \
  --sell-price 2510.00
```

### Output

```
======================== PROFIT BREAKDOWN ========================

Trade: 50 ETH
Buy on binance at $2,500.00
Sell on coinbase at $2,510.00

Gross Profit: $500.00 (+0.400%)

Costs:
  Buy fee:        -$12.50
  Sell fee:       -$75.30
  Withdrawal:     -$6.25
  Gas:            -$0.00
  Slippage:       -$12.50
  ------------------------------
  Total:          -$106.55

Net Profit: $393.45 (+0.315%)
Breakeven spread: 0.085%

✓ PROFITABLE
```

---

## Example 8: JSON Output

Export results in JSON format for programmatic use.

### Command

```bash
python arb_finder.py scan ETH USDC --output json
```

### Output

```json
{
  "pair": "ETH/USDC",
  "timestamp": 1705968000,
  "quotes_count": 9,
  "opportunities_count": 3,
  "quotes": [
    {
      "exchange": "coinbase",
      "exchange_type": "cex",
      "bid": 2543.80,
      "ask": 2544.10,
      "spread_pct": 0.012,
      "volume_24h": 125000000.0
    }
  ],
  "opportunities": [
    {
      "buy_exchange": "balancer",
      "sell_exchange": "coinbase",
      "buy_price": 2540.30,
      "sell_price": 2543.80,
      "gross_spread_pct": 0.1378,
      "net_spread_pct": 0.0368,
      "risk_level": "low",
      "is_profitable": true
    }
  ],
  "best_opportunity": {
    "buy_exchange": "balancer",
    "sell_exchange": "coinbase",
    "buy_price": 2540.30,
    "sell_price": 2543.80,
    "net_spread_pct": 0.0368,
    "risk_level": "low"
  }
}
```

---

## Example 9: DEX-Only Scan

Scan only decentralized exchanges.

### Command

```bash
python arb_finder.py scan ETH USDC --dex-only
```

### Output

```
======================== ARBITRAGE SCAN RESULTS ========================

Pair: ETH/USDC
Exchanges scanned: 4
Opportunities found: 2

----------------------------------------------------------------------
CURRENT PRICES
----------------------------------------------------------------------
Exchange        Bid             Ask         Spread
----------------------------------------------------------------------
Uniswap V3      $2,543.50       $2,544.00   0.020%
SushiSwap       $2,540.50       $2,541.00   0.020%
Curve           $2,540.20       $2,540.60   0.016%
Balancer        $2,539.80       $2,540.30   0.020%

----------------------------------------------------------------------
OPPORTUNITIES
----------------------------------------------------------------------
Buy On          Sell On         Gross    Net      Risk
----------------------------------------------------------------------
Balancer        Uniswap V3      +0.126%  +0.062%  🟢 LOW
Curve           Uniswap V3      +0.114%  +0.050%  🟢 LOW

----------------------------------------------------------------------
BEST OPPORTUNITY
----------------------------------------------------------------------
Buy on Balancer at $2,540.30
Sell on Uniswap V3 at $2,543.50

Gross spread: +0.1260%
Buy fee: -0.10%
Sell fee: -0.30%
Gas cost: ~$22.50 (2 swaps)
----------------------------------------------------------------------
Net spread: +0.0620%
Risk: 🟢 LOW

Notes:
  • Both DEX - can execute atomically via flash loan
  • Gas costs for 2 swap operations included

✓ PROFITABLE - Consider execution
```

---

## Example 10: Custom Gas Price

Adjust calculations for different gas conditions.

### Command

```bash
python arb_finder.py scan ETH USDC --dex-only --gas-price 100 --eth-price 3000
```

### Output

```
======================== ARBITRAGE SCAN RESULTS ========================

Pair: ETH/USDC
Exchanges scanned: 4
Opportunities found: 0

----------------------------------------------------------------------
CURRENT PRICES
----------------------------------------------------------------------
Exchange        Bid             Ask         Spread
----------------------------------------------------------------------
Uniswap V3      $2,543.50       $2,544.00   0.020%
SushiSwap       $2,540.50       $2,541.00   0.020%
Curve           $2,540.20       $2,540.60   0.016%
Balancer        $2,539.80       $2,540.30   0.020%

No profitable opportunities found (market is efficient)

Note: High gas price ($45.00 per swap) makes small spreads unprofitable.
      Consider waiting for lower gas or targeting larger spreads.
```

---

## Common Patterns

### Morning Scan Routine

```bash
# Quick overview of major pairs
python arb_finder.py scan BTC USDT --cex-only
python arb_finder.py scan ETH USDC --cex-only
python arb_finder.py scan ETH BTC --cex-only
```

### Continuous Monitoring

```bash
# Run in tmux/screen for persistent monitoring
python arb_finder.py monitor ETH USDC --threshold 0.2 --interval 10
```

### Export for Analysis

```bash
# Save to file for later analysis
python arb_finder.py scan ETH USDC --output json > arb_$(date +%Y%m%d).json
```

### Triangular Sweep

```bash
# Check all major exchanges for triangular opportunities
for exchange in binance coinbase kraken; do
  echo "=== $exchange ==="
  python arb_finder.py triangular $exchange --min-profit 0.0
done
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
