# Implementation Details

## Trade Size Recommendations

| Trade Size | Strategy | Notes |
|------------|----------|-------|
| < $1K | Direct quote | Gas may exceed savings from optimization |
| $1K - $10K | Compare + routes | Multi-hop can save 0.1-0.5% |
| $10K - $100K | Split analysis | 2-3 way splits reduce price impact |
| > $100K | Full + MEV + private TX | Consider OTC or algorithmic execution |

## Split Order Optimization

For large trades ($10K+), the router calculates optimal allocation across venues:

```
Split Recommendation:
  60% via Uniswap V3  (60 ETH -> 152,589 USDC)
  40% via Curve       (40 ETH -> 101,843 USDC)
  ─────────────────────────────────────────────
  Total: 254,432 USDC (vs. 251,200 single-venue)
  Improvement: +1.28% ($3,232 saved)
```

The optimization algorithm:
1. Queries each venue for the full trade amount to measure price impact curves
2. Uses gradient descent to find the allocation that minimizes total slippage
3. Accounts for gas costs of multiple transactions (splitting adds ~$5-15 per venue)
4. Only recommends splitting when savings exceed additional gas overhead

## Output Mode Details

**Quick Quote Mode:**
- Best price across aggregators, output amount, effective rate, gas estimate, recommended venue

**Comparison Mode (`--compare`):**
- All venues ranked by effective rate (price minus gas)
- Price impact percentage per venue
- Gas costs compared in USD
- Liquidity depth indicators (shallow/moderate/deep)

**Route Analysis (`--routes`):**
- Direct vs. multi-hop comparison
- Hop-by-hop breakdown with intermediate tokens
- Cumulative price impact at each hop
- Gas cost per route type

**Split Mode (`--split`):**
- Optimal allocation percentages across venues
- Per-venue output amounts
- Total vs. single-venue comparison
- Dollar savings estimate

**MEV Assessment (`--mev-check`):**
- Risk score: LOW/MEDIUM/HIGH
- Estimated sandwich attack exposure in USD
- Protection recommendations (Flashbots Protect, CoW Swap, private mempool)
- Alternative MEV-resistant venues

## MEV Risk Scoring

The MEV check analyzes:
- **Token pair popularity**: High-volume pairs attract more MEV bots
- **Trade size relative to pool**: Larger trades = more profitable to sandwich
- **Current mempool activity**: Active searcher presence
- **Slippage tolerance**: Higher tolerance = more extractable value

Risk levels:
- **LOW** (score 0-30): Safe to execute via public mempool
- **MEDIUM** (score 31-70): Consider private transaction relay
- **HIGH** (score 71-100): Use Flashbots Protect or CoW Swap batch auctions

## API Configuration

Edit `${CLAUDE_SKILL_DIR}/config/settings.yaml`:
```yaml
api_keys:
  oneinch: "your-1inch-api-key"    # Optional, increases rate limits
  zerox: "your-0x-api-key"         # Optional

chain: ethereum                     # Default: ethereum, arbitrum, polygon, optimism

aggregators:
  - name: 1inch
    enabled: true
    timeout: 10
  - name: paraswap
    enabled: true
    timeout: 10
  - name: zerox
    enabled: true
    timeout: 10
```
