# Flash Loan Simulator - Examples

## Quick Start Examples

### Example 1: Simple ETH/USDC Arbitrage

Simulate buying ETH on SushiSwap and selling on Uniswap:

```bash
python flash_simulator.py arbitrage ETH USDC 100 \
  --dex-buy sushiswap \
  --dex-sell uniswap \
  --provider aave
```

**Expected Output:**

```
==================== FLASH LOAN SIMULATION ====================

┌─────────────────────────── SUMMARY ────────────────────────────┐
│ Strategy: SIMPLE_ARBITRAGE                                     │
│ Loan: 100 ETH                                                  │
│ Provider: aave                                                 │
│ Profitable: YES ✓                                              │
└────────────────────────────────────────────────────────────────┘

----------------------------------------------------------------------
TRANSACTION STEPS
----------------------------------------------------------------------

  1. [Aave] flash_loan
     ETH → ETH
     100.000000 → 100.000000
     Gas: ~100,000 units

  2. [SushiSwap] swap
     ETH → USDC
     100.000000 → 253850.000000
     Gas: ~150,000 units

  3. [Uniswap] swap
     USDC → ETH
     253850.000000 → 100.188120
     Gas: ~150,000 units

  4. [Aave] repay
     ETH → ETH
     100.090000 → 100.090000
     Gas: ~50,000 units

----------------------------------------------------------------------
PROFIT BREAKDOWN
----------------------------------------------------------------------
  Gross Profit:  +0.188120 ETH
  Flash Loan Fee: -0.090000 ETH
  Gas Cost:       -0.013500 ETH ($33.75)
  ────────────────────────────────────────
  Net Profit:    +0.084620 ETH ($211.55)
  ROI:           0.0846%
```

---

### Example 2: Compare Flash Loan Providers

Find the cheapest provider for a 100 ETH loan:

```bash
python flash_simulator.py compare ETH 100
```

**Expected Output:**

```
=================== PROVIDER COMPARISON ===================

  Comparing 100 ETH flash loan:

  Provider       Fee %    Fee Amount     Gas OH     Chains
  ------------------------------------------------------------------
  dYdX           0.00%    0.0000 ETH     150,000    ethereum
  Balancer       0.01%    0.0100 ETH     80,000     ethereum, polygon...
  Aave V3        0.09%    0.0900 ETH     100,000    ethereum, polygon...
  Uniswap V3     0.30%    0.3000 ETH     120,000    ethereum, polygon...

  Recommended: dYdX
  (FREE flash loan!)
```

---

### Example 3: Full Analysis with Risk Assessment

Run a complete analysis with provider comparison and risk scoring:

```bash
python flash_simulator.py arbitrage ETH USDC 100 --full
```

**Expected Output:**

```
==================== FLASH LOAN SIMULATION ====================
[... strategy result ...]

==================== PROFIT BREAKDOWN ====================

  Gross Revenue: 0.188120 ETH

  Costs:
    Flash Loan Fee: -0.090000 ETH
    Gas Cost:       -0.013500 ETH ($33.75)
    Est. Slippage:  -0.500000 ETH
    DEX Fees:       ~0.600000 ETH (in price)
    ─────────────────────────────────────────────
    Total Costs:    -0.603500 ETH

  Net Profit: -0.415380 ETH (-$1038.45)
  ROI: -0.4154%
  Breakeven Gas: 0.0 gwei

  ✗ NOT PROFITABLE

==================== RISK ASSESSMENT ====================

  Overall Risk: 🟠 HIGH
  Risk Score: 65/100
  Viability: CAUTION

----------------------------------------------------------------------
RISK FACTORS
----------------------------------------------------------------------

  🔴 MEV Competition: CRITICAL (90)
     High bot activity on ETH pairs
     → Use Flashbots Protect or private transactions

  🟡 Execution Risk: MEDIUM (45)
     4 steps with gas-sensitive timing
     → Set tight slippage tolerance; use gas price oracles

  🟢 Protocol Risk: LOW (18)
     Using 2 protocol(s): aave, sushiswap
     → Verify protocol audits; monitor for exploits

  🟡 Liquidity Risk: MEDIUM (35)
     $250,000 trade may cause significant slippage
     → Check pool liquidity; consider splitting order

  🔴 Profit Margin: CRITICAL (100)
     -0.415% profit margin (NEGATIVE!)
     → Increase trade size or wait for better opportunity

----------------------------------------------------------------------
WARNINGS
----------------------------------------------------------------------
  ⚠️  MEV Competition: High bot activity on ETH pairs
  ⚠️  Profit Margin: -0.415% profit margin (NEGATIVE!)

----------------------------------------------------------------------
RECOMMENDATIONS
----------------------------------------------------------------------
  • Use Flashbots Protect to avoid sandwich attacks
  • Consider private transaction submission
  • Strategy is UNPROFITABLE - do not execute
```

---

### Example 4: Triangular Arbitrage

Simulate a three-hop circular arbitrage:

```bash
python flash_simulator.py triangular ETH USDC WBTC ETH --amount 50
```

**Expected Output:**

```
==================== FLASH LOAN SIMULATION ====================

┌─────────────────────────── SUMMARY ────────────────────────────┐
│ Strategy: TRIANGULAR_ARBITRAGE                                 │
│ Loan: 50 ETH                                                   │
│ Provider: aave                                                 │
│ Profitable: YES ✓                                              │
└────────────────────────────────────────────────────────────────┘

----------------------------------------------------------------------
TRANSACTION STEPS
----------------------------------------------------------------------

  1. [Aave] flash_loan
     ETH → ETH
     50.000000 → 50.000000
     Gas: ~100,000 units

  2. [Uniswap] swap
     ETH → USDC
     50.000000 → 127500.000000
     Gas: ~150,000 units

  3. [Curve] swap
     USDC → WBTC
     127500.000000 → 1.870000
     Gas: ~200,000 units

  4. [SushiSwap] swap
     WBTC → ETH
     1.870000 → 50.120000
     Gas: ~150,000 units

  5. [Aave] repay
     ETH → ETH
     50.045000 → 50.045000
     Gas: ~50,000 units

----------------------------------------------------------------------
PROFIT BREAKDOWN
----------------------------------------------------------------------
  Gross Profit:  +0.120000 ETH
  Flash Loan Fee: -0.045000 ETH
  Gas Cost:       -0.019500 ETH ($48.75)
  ────────────────────────────────────────
  Net Profit:    +0.055500 ETH ($138.75)
  ROI:           0.1110%
```

---

### Example 5: Liquidation Simulation

Analyze a potential Aave liquidation opportunity:

```bash
python flash_simulator.py liquidation \
  --protocol aave \
  --collateral ETH \
  --debt USDC \
  --amount 10000 \
  --health-factor 0.95
```

**Expected Output:**

```
==================== FLASH LOAN SIMULATION ====================

┌─────────────────────────── SUMMARY ────────────────────────────┐
│ Strategy: LIQUIDATION                                          │
│ Loan: 10000 USDC                                               │
│ Provider: aave                                                 │
│ Profitable: YES ✓                                              │
└────────────────────────────────────────────────────────────────┘

----------------------------------------------------------------------
TRANSACTION STEPS
----------------------------------------------------------------------

  1. [Aave] flash_loan
     USDC → USDC
     10000.000000 → 10000.000000
     Gas: ~100,000 units

  2. [Aave] liquidation_call
     USDC → ETH
     10000.000000 → 4.200000
     Gas: ~300,000 units

  3. [Uniswap] swap
     ETH → USDC
     4.200000 → 10710.000000
     Gas: ~150,000 units

  4. [Aave] repay
     USDC → USDC
     10009.000000 → 10009.000000
     Gas: ~50,000 units

----------------------------------------------------------------------
PROFIT BREAKDOWN
----------------------------------------------------------------------
  Gross Profit:  +710.000000 USDC
  Flash Loan Fee: -9.000000 USDC
  Gas Cost:       -18.000000 USDC
  ────────────────────────────────────────
  Net Profit:    +683.000000 USDC ($683.00)
  ROI:           6.8300%
```

---

### Example 6: JSON Output for Integration

Export simulation results as JSON for programmatic use:

```bash
python flash_simulator.py arbitrage ETH USDC 100 --full --output json > simulation.json
```

**Example JSON Output:**

```json
{
  "simulation": {
    "strategy_type": "SIMPLE_ARBITRAGE",
    "loan_asset": "ETH",
    "loan_amount": 100.0,
    "provider": "aave",
    "is_profitable": true
  },
  "profit": {
    "gross_profit": 0.18812,
    "loan_fee": 0.09,
    "gas_cost_eth": 0.0135,
    "gas_cost_usd": 33.75,
    "net_profit": 0.08462,
    "net_profit_usd": 211.55,
    "roi_percent": 0.0846
  },
  "steps": [
    {
      "protocol": "Aave",
      "action": "flash_loan",
      "asset_in": "ETH",
      "asset_out": "ETH",
      "amount_in": 100.0,
      "amount_out": 100.0,
      "gas_estimate": 100000
    }
  ],
  "risk": {
    "overall_level": "HIGH",
    "overall_score": 65.0,
    "viability": "CAUTION",
    "factors": [
      {
        "name": "MEV Competition",
        "level": "CRITICAL",
        "score": 90.0,
        "description": "High bot activity on ETH pairs",
        "mitigation": "Use Flashbots Protect or private transactions"
      }
    ],
    "warnings": ["MEV Competition: High bot activity on ETH pairs"],
    "recommendations": ["Use Flashbots Protect to avoid sandwich attacks"]
  },
  "providers": [
    {
      "name": "dYdX",
      "fee_rate": 0.0,
      "fee_amount": 0.0,
      "max_available": 50000.0,
      "gas_overhead": 150000,
      "supported_chains": ["ethereum"]
    }
  ]
}
```

---

### Example 7: Using dYdX for Zero-Fee Loans

Maximize profit by using dYdX's free flash loans:

```bash
python flash_simulator.py arbitrage ETH USDC 100 \
  --provider dydx \
  --dex-buy sushiswap \
  --dex-sell uniswap \
  --risk-analysis
```

**Key Difference:**

- Flash loan fee: 0.00 ETH (vs 0.09 ETH with Aave)
- Net profit increases by ~$225

---

### Example 8: Custom Gas and ETH Price

Simulate with current market conditions:

```bash
python flash_simulator.py arbitrage ETH USDC 100 \
  --eth-price 3500 \
  --gas-price 50 \
  --full
```

This adjusts:

- All USD calculations use $3,500/ETH
- Gas costs calculated at 50 gwei
- Breakeven gas price recalculated

---

## Programmatic Usage

### Python Script Example

```python
#!/usr/bin/env python3
"""Example: Run multiple simulations programmatically."""

from decimal import Decimal
from strategy_engine import StrategyFactory, StrategyType, ArbitrageParams
from profit_calculator import ProfitCalculator
from risk_assessor import RiskAssessor
from protocol_adapters import ProviderManager

def analyze_arbitrage_opportunity(
    input_token: str,
    output_token: str,
    amount: float,
    dex_buy: str,
    dex_sell: str,
) -> dict:
    """Analyze an arbitrage opportunity across all providers."""

    factory = StrategyFactory()
    calculator = ProfitCalculator(eth_price_usd=2500.0, gas_price_gwei=30.0)
    assessor = RiskAssessor(eth_price_usd=2500.0)
    manager = ProviderManager()

    results = []

    for provider_name in manager.list_providers():
        strategy = factory.create(StrategyType.SIMPLE_ARBITRAGE)

        params = ArbitrageParams(
            input_token=input_token,
            output_token=output_token,
            amount=Decimal(str(amount)),
            dex_buy=dex_buy,
            dex_sell=dex_sell,
            provider=provider_name,
        )

        result = strategy.simulate(params)
        breakdown = calculator.calculate_breakdown(result)
        assessment = assessor.assess(result)

        results.append({
            "provider": provider_name,
            "net_profit_eth": float(result.net_profit),
            "net_profit_usd": float(result.net_profit_usd),
            "roi_percent": result.roi_percent,
            "risk_score": assessment.overall_score,
            "viability": assessment.viability,
            "is_profitable": result.is_profitable,
        })

    # Sort by net profit
    results.sort(key=lambda x: x["net_profit_usd"], reverse=True)

    return {
        "opportunity": f"{input_token}/{output_token}",
        "amount": amount,
        "best_provider": results[0]["provider"] if results else None,
        "providers": results,
    }


if __name__ == "__main__":
    # Analyze ETH/USDC arbitrage opportunity
    analysis = analyze_arbitrage_opportunity(
        input_token="ETH",
        output_token="USDC",
        amount=100,
        dex_buy="sushiswap",
        dex_sell="uniswap",
    )

    print(f"Best provider: {analysis['best_provider']}")
    for p in analysis["providers"]:
        print(
            f"  {p['provider']}: ${p['net_profit_usd']:.2f} "
            f"(Risk: {p['risk_score']:.0f}, {p['viability']})"
        )
```

---

## Integration Patterns

### Batch Analysis

```bash
# Analyze multiple pairs
for pair in "ETH-USDC" "WBTC-ETH" "ETH-DAI"; do
  IFS='-' read -r input output <<< "$pair"
  python flash_simulator.py arbitrage $input $output 100 --output json
done
```

### Pipeline Integration

```bash
# Feed into analysis pipeline
python flash_simulator.py arbitrage ETH USDC 100 --output json | \
  jq '.risk.viability == "GO"'
```

### Automated Monitoring

```bash
# Check profitability every minute
while true; do
  result=$(python flash_simulator.py arbitrage ETH USDC 100 --output json)
  profitable=$(echo "$result" | jq '.simulation.is_profitable')
  if [ "$profitable" = "true" ]; then
    echo "PROFITABLE OPPORTUNITY DETECTED"
    echo "$result" | jq '.profit'
  fi
  sleep 60
done
```

---

## Disclaimer

All examples are for educational purposes only. Flash loan strategies involve significant risks:

1. **Smart Contract Risk**: Bugs can cause total loss
2. **MEV Risk**: Bots may front-run your transactions
3. **Execution Risk**: Gas prices can spike unexpectedly
4. **Market Risk**: Prices change between simulation and execution

Always:

- Test on testnets first
- Start with small amounts
- Use MEV protection in production
- Verify protocol audits

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
