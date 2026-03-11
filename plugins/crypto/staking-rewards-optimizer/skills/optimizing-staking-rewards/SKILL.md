---
name: optimizing-staking-rewards
description: |
  Compare and optimize staking rewards across validators, protocols, and blockchains with risk assessment.
  Use when analyzing staking opportunities, comparing validators, calculating staking rewards, or optimizing PoS yields.
  Trigger with phrases like "optimize staking", "compare staking", "best staking APY", "liquid staking", "validator comparison", "staking rewards", or "ETH staking options".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:staking-*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Optimizing Staking Rewards

## Overview

This skill analyzes staking opportunities across multiple proof-of-stake blockchains and liquid staking protocols. It compares APY/APR, calculates net yields after fees, assesses protocol risks, and provides optimization recommendations for maximizing staking returns.

Key capabilities:
- Compare native and liquid staking options across chains
- Calculate true APY after protocol fees and gas costs
- Assess risk factors for each staking protocol
- Optimize portfolio allocation across staking opportunities
- Project returns over custom time horizons

## Prerequisites

Before using this skill, ensure you have:
- Python 3.8+ installed
- `requests` library for API calls (`pip install requests`)
- Network access to DeFiLlama APIs
- Basic understanding of staking concepts (APY, validators, unbonding)

Optional:
- CoinGecko API key for higher rate limits on price data

## Instructions

### Step 1: Compare Staking Opportunities

To compare staking options for a specific asset:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --asset ETH
```

This fetches current rates from DeFiLlama and displays:
- Protocol name and type (native vs liquid)
- Gross APY (advertised rate)
- Net APY (after protocol fees)
- Risk score (1-10, where 10 is safest)
- TVL and lock-up period

### Step 2: Analyze with Position Size

For gas-adjusted yields based on your stake amount:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --asset ETH --amount 10
```

Adding `--amount` calculates:
- Effective APY accounting for gas costs
- Projected returns (1M, 3M, 6M, 1Y)
- Gas cost as percentage of position

### Step 3: Optimize Existing Portfolio

Input current positions for optimization recommendations:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --optimize \
  --positions "10 ETH @ lido 4.0%, 100 ATOM @ native 18%, 50 DOT @ native 14%"
```

The optimizer will:
- Calculate current total yield
- Suggest higher-yield alternatives
- Show projected improvement
- Warn about switching costs

### Step 4: Compare Specific Protocols

For head-to-head protocol comparison:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --compare --protocols lido,rocket-pool,frax-ether
```

Compare metrics:
- APY side-by-side
- Fee structures
- Risk profiles
- Liquidity depth

### Step 5: Detailed Risk Assessment

For in-depth protocol analysis:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --asset ETH --detailed
```

Shows for each protocol:
- Audit status and age
- Time in production
- Validator diversity
- Historical performance
- Slashing incidents

### Step 6: Export Results

Save analysis for further use:

```bash
# JSON output
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --asset ETH --format json --output staking.json

# CSV for spreadsheets
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --asset ETH --format csv --output staking.csv
```

## Output

### Quick Comparison Table

```
==============================================================================
  STAKING REWARDS OPTIMIZER                              2025-01-15 15:30 UTC
==============================================================================

  STAKING OPTIONS FOR ETH
------------------------------------------------------------------------------
  Protocol        Type      Gross APY  Net APY  Risk   TVL         Unbond
------------------------------------------------------------------------------
  Frax (sfrxETH)  liquid      5.10%     4.59%   7/10   $450M       instant
  Lido (stETH)    liquid      4.00%     3.60%   9/10   $15B        instant
  Rocket Pool     liquid      4.20%     3.61%   8/10   $3B         instant
  Coinbase cbETH  liquid      3.80%     3.42%   9/10   $2B         instant
  ETH Native      native      4.00%     4.00%   10/10  $50B        variable
------------------------------------------------------------------------------
  Ranked by risk-adjusted return (Net APY × Risk Score / 10)
==============================================================================
```

### Optimization Report

```
==============================================================================
  PORTFOLIO OPTIMIZATION
==============================================================================

  CURRENT PORTFOLIO
------------------------------------------------------------------------------
  Position              APY      Annual Return
  10 ETH @ Lido         3.60%    $720
  100 ATOM @ Native     18.00%   $3,600
  50 DOT @ Native       14.00%   $1,400
------------------------------------------------------------------------------
  Total Portfolio: $25,000      Blended APY: 22.88%    Annual: $5,720

  OPTIMIZED ALLOCATION
------------------------------------------------------------------------------
  Recommendation        APY      Annual Return   Change
  10 ETH → Frax         4.59%    $918           +$198
  100 ATOM → Keep       18.00%   $3,600         $0
  50 DOT → Keep         14.00%   $1,400         $0
------------------------------------------------------------------------------
  Optimized Annual: $5,918      Improvement: +$198 (+3.5%)

  IMPLEMENTATION
  1. Unstake 10 ETH from Lido (instant - liquid)
  2. Swap stETH → ETH on Curve (0.01% slippage est.)
  3. Stake ETH for sfrxETH on Frax Finance
  4. Est. gas cost: ~$15 (current gas: 25 gwei)
==============================================================================
```

### Risk Assessment Detail

```
  RISK ASSESSMENT: Lido (stETH)
------------------------------------------------------------------------------
  Overall Score: 9/10 (Low Risk)

  Breakdown:
  - Audit Status:        ✓ Multiple audits, latest 6 months ago (+2.0)
  - Time in Production:  ✓ 3+ years live (+2.0)
  - TVL Size:            ✓ $15B+ locked (+2.0)
  - Protocol Reputation: ✓ Industry standard, DAO governance (+1.5)
  - Validator Diversity: ✓ 30+ validators (+1.5)

  Considerations:
  - Largest LSD by market share (potential centralization concerns)
  - stETH occasionally trades at slight discount to ETH
  - 10% fee on staking rewards

  Historical:
  - No slashing events to date
  - stETH peg maintained through market stress
  - Consistent validator performance
------------------------------------------------------------------------------
```

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

Common issues:
- **API timeout**: Cached data used, shown with warning
- **Invalid asset**: Lists supported assets
- **Rate limited**: Automatic retry with backoff
- **No data found**: Falls back to known protocol list

## Examples

### Example 1: Quick Comparison
```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --asset ETH
# Shows all ETH staking options ranked by risk-adjusted return
```

### Example 2: Large Position Analysis
```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --asset ETH --amount 100 --detailed
# Shows gas-adjusted yields for 100 ETH with full risk analysis
```

### Example 3: Multi-Asset Research
```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --assets ETH,SOL,ATOM --format csv
# Compares staking across multiple assets, exports to CSV
```

### Example 4: Portfolio Optimization
```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --optimize \
  --positions "50 ETH @ lido 3.6%, 500 SOL @ marinade 7.5%"
# Analyzes current positions and suggests improvements
```

### Example 5: Protocol Deep Dive
```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --protocol rocket-pool --detailed
# Full analysis of Rocket Pool including validator metrics
```

## Resources

- **DeFiLlama Yields**: https://defillama.com/yields - Primary data source
- **StakingRewards**: https://www.stakingrewards.com - Native staking reference
- **Lido**: https://lido.fi - Largest liquid staking protocol
- **Rocket Pool**: https://rocketpool.net - Decentralized ETH staking
- **Frax Finance**: https://frax.finance - sfrxETH liquid staking
- **Marinade**: https://marinade.finance - Solana liquid staking

## Important Notes

- APYs are variable and change based on network participation
- Historical yields do not guarantee future returns
- This tool provides information, not financial advice
- Always DYOR (Do Your Own Research) before staking
- Consider your risk tolerance and liquidity needs
