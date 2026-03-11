# Tracking Crypto Derivatives - Implementation Reference

## Detailed Output Formats

### Funding Rate Report
```
BTC PERPETUAL FUNDING RATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exchange    Current    24h Avg    7d Avg    Next Payment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Binance     +0.0150%   +0.0120%   +0.0080%  2h 15m
Bybit       +0.0180%   +0.0140%   +0.0100%  2h 15m
OKX         +0.0130%   +0.0110%   +0.0090%  2h 15m
Deribit     +0.0200%   +0.0150%   +0.0120%  2h 15m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Weighted Avg: +0.0158%  |  Annualized: +17.29%
Sentiment: Moderately Bullish
```

### Open Interest Report
```
BTC OPEN INTEREST ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exchange    OI (USD)      24h Chg    7d Chg    Share
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Binance     $8.2B         +2.5%      +8.1%     44.3%
Bybit       $4.5B         +1.8%      +5.2%     24.3%
OKX         $3.1B         +3.2%      +12.5%    16.8%
BitMEX      $1.5B         -0.5%      -2.1%     8.1%
Deribit     $1.2B         +0.8%      +3.4%     6.5%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total OI: $18.5B (+2.3% 24h)
Long/Short Ratio: 1.15 (53.5% long)
```

### Liquidation Heatmap
```
BTC LIQUIDATION LEVELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: $67,500

LONG LIQUIDATIONS (below):
  $65,000 ████████████ $125M (HIGH DENSITY)
  $62,500 ███████      $85M
  $60,000 ████████████████████ $210M (CRITICAL)

SHORT LIQUIDATIONS (above):
  $70,000 █████████    $95M
  $72,500 █████████████ $145M (HIGH DENSITY)
  $75,000 █████████████████ $180M
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
24h Liquidations: Longs $45.2M | Shorts $32.8M
```

## Options Analysis Deep Dive

### Options Commands
```bash
# Get options overview
python derivatives_tracker.py options BTC

# Show put/call ratio
python derivatives_tracker.py options BTC --pcr

# Find max pain for expiry
python derivatives_tracker.py options BTC --expiry 2025-01-31

# Track large options trades
python derivatives_tracker.py options BTC --flow
```

### Options Insights
- **High IV rank** (>80): Options expensive, consider selling
- **Low IV rank** (<20): Options cheap, consider buying
- **Max pain**: Price where most options expire worthless

## Basis Trading Guide

### Basis Commands
```bash
# Get spot-perp basis
python derivatives_tracker.py basis BTC

# Get quarterly futures basis
python derivatives_tracker.py basis BTC --quarterly

# Show all basis opportunities
python derivatives_tracker.py basis --all
```

### Basis Trading Interpretation
- **Positive basis**: Futures > Spot (contango, normal)
- **Negative basis**: Futures < Spot (backwardation)
- **Cash-and-carry**: Buy spot + sell futures when basis high

## Key Concepts

- **Funding Rate**: Payment between longs/shorts every 8h
- **Open Interest**: Total outstanding contracts
- **Basis**: Difference between futures and spot price
- **Max Pain**: Strike where most options expire worthless
- **IV Rank**: Current IV percentile vs historical

## Risk Warning

Derivatives are leveraged instruments with high risk of loss.
- Funding costs accumulate over time
- Liquidations can happen rapidly
- Options can expire worthless
- This tool provides analysis only, not financial advice
