# Implementation Details

## Flash Loan Provider Comparison

| Provider | Fee | Best For | Chains |
|----------|-----|----------|--------|
| dYdX | 0% | Maximum profit | Ethereum |
| Balancer | 0.01% | Pool tokens | ETH, Polygon, Arbitrum |
| Aave V3 | 0.09% | Any token | ETH, Polygon, Arbitrum, Optimism |
| Uniswap V3 | ~0.3% | Specific pairs | ETH, Polygon, Arbitrum |

## Supported Strategies

1. **Simple Arbitrage**: Buy on DEX A, sell on DEX B. Requires price discrepancy > fees + gas.
2. **Triangular Arbitrage**: A->B->C->A circular path. More complex but finds hidden opportunities.
3. **Liquidation**: Repay underwater debt, claim collateral bonus (typically 5-15% on Aave).
4. **Collateral Swap**: Replace collateral without closing position. Useful for risk rotation.
5. **Self-Liquidation**: Efficiently close own position when health factor is low.
6. **Debt Refinancing**: Move debt to better rates across protocols.

## Triangular Arbitrage Output Breakdown

```
Path: ETH -> USDC -> WBTC -> ETH
Gross: +0.15 ETH
Fees:  -0.045 ETH (3 swaps)
Loan:  -0.045 ETH (Aave fee)
Gas:   -0.02 ETH
---------------------
Net:   +0.04 ETH ($101.73)
```

## Risk Analysis Scoring

When `--risk-analysis` is enabled, four risk factors are scored 0-100:

- **MEV Competition** (0-100): Measures bot activity on the token pair. Score > 70 means heavy competition from established searchers.
- **Execution Risk** (0-100): Slippage sensitivity and timing requirements. Higher scores mean tighter execution windows.
- **Protocol Risk** (0-100): Smart contract maturity, audit status, oracle reliability. Lower is safer.
- **Liquidity Risk** (0-100): Whether pool depth supports the trade size. Score > 80 means trade may move price significantly.

Overall viability grades:
- **A**: All risks low, high confidence
- **B**: Moderate risks, proceed with caution
- **C**: High risks, likely unprofitable
- **F**: Do not attempt

## Output Modes

**Quick Mode** (default):
- Net profit/loss, provider recommendation, Go/No-Go verdict

**Breakdown Mode** (`--breakdown`):
- Step-by-step transaction flow, individual cost components, slippage estimates

**Comparison Mode** (`--compare-providers`):
- All providers ranked by net profit, fee differences, liquidity availability

**Risk Analysis** (`--risk-analysis`):
- Competition score, execution probability, protocol safety, overall viability grade

## Educational Disclaimer

**FOR EDUCATIONAL PURPOSES ONLY.** Flash loan strategies involve significant risks:
- Smart contract bugs can cause total loss of borrowed funds
- MEV bots compete for the same opportunities with faster infrastructure
- Gas costs can exceed profits, especially during network congestion
- Protocol exploits may have legal implications

Never deploy unaudited code. Start with testnets. Consult legal counsel for compliance.
