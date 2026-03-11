# Optimizing Staking Rewards - Implementation Reference

## Optimization Report Output

When using `--optimize`, the tool generates a full portfolio optimization:

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
  10 ETH -> Frax        4.59%    $918           +$198
  100 ATOM -> Keep      18.00%   $3,600         $0
  50 DOT -> Keep        14.00%   $1,400         $0
------------------------------------------------------------------------------
  Optimized Annual: $5,918      Improvement: +$198 (+3.5%)

  IMPLEMENTATION
  1. Unstake 10 ETH from Lido (instant - liquid)
  2. Swap stETH -> ETH on Curve (0.01% slippage est.)
  3. Stake ETH for sfrxETH on Frax Finance
  4. Est. gas cost: ~$15 (current gas: 25 gwei)
==============================================================================
```

## Risk Assessment Detail

Detailed risk output (with `--detailed` flag):

```
  RISK ASSESSMENT: Lido (stETH)
------------------------------------------------------------------------------
  Overall Score: 9/10 (Low Risk)

  Breakdown:
  - Audit Status:        Multiple audits, latest 6 months ago (+2.0)
  - Time in Production:  3+ years live (+2.0)
  - TVL Size:            $15B+ locked (+2.0)
  - Protocol Reputation: Industry standard, DAO governance (+1.5)
  - Validator Diversity:  30+ validators (+1.5)

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

## Protocol Deep Dive

Use `--protocol <name> --detailed` for full protocol analysis including:
- Validator count and diversity metrics
- Fee structure breakdown
- Historical APY trends
- Smart contract audit history
- Slashing incident reports

```bash
python ${CLAUDE_SKILL_DIR}/scripts/staking_optimizer.py --protocol rocket-pool --detailed
```

## Important Notes

- APYs are variable and change based on network participation
- Historical yields do not guarantee future returns
- This tool provides information, not financial advice
- Always DYOR (Do Your Own Research) before staking
- Consider your risk tolerance and liquidity needs
