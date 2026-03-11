---
name: scanning-market-movers
description: |
  Detect significant price movements and unusual volume across crypto markets.
  Calculates significance scores combining price change, volume ratio, and market cap.
  Use when tracking market movers, finding gainers/losers, or detecting volume spikes.
  Trigger with phrases like "scan market movers", "top gainers", "biggest losers",
  "volume spikes", "what's moving", "find pumps", or "market scan".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Scanning Market Movers

## Overview

Real-time detection and analysis of significant price movements and unusual volume patterns across cryptocurrency markets. This skill identifies top gainers, losers, and volume spikes, ranking them by a composite significance score.

**Key Features:**
- Scan 1,000+ cryptocurrencies for movers
- Configurable thresholds (change %, volume spike, market cap)
- Significance scoring for prioritization
- Category filtering (DeFi, L2, NFT, etc.)
- Multiple output formats (table, JSON, CSV)

**Dependency:**
This skill uses `tracking-crypto-prices` from `market-price-tracker` plugin for price data infrastructure.

## Prerequisites

Install required dependencies:

```bash
pip install requests pandas
```

**Dependency Setup:**
Ensure `market-price-tracker` plugin is installed with `tracking-crypto-prices` skill configured.

## Instructions

### Step 1: Quick Market Scan

Run a default scan for top gainers and losers:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py
```

This returns the top 20 gainers and top 20 losers by 24h change with volume confirmation.

### Step 2: Custom Thresholds

Scan with specific criteria:

```bash
# Only show moves > 10% with volume spike > 3x
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-change 10 --volume-spike 3

# Filter by market cap
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-cap 100000000 --max-cap 1000000000
```

### Step 3: Category Filtering

Focus on specific sectors:

```bash
# DeFi tokens only
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --category defi

# Layer 2 tokens
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --category layer2

# Available: defi, layer2, nft, gaming, meme
```

### Step 4: Different Timeframes

Scan across timeframes:

```bash
# 1-hour movers
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --timeframe 1h

# 7-day movers
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --timeframe 7d
```

### Step 5: Export Results

Save results for analysis:

```bash
# JSON export
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --format json --output movers.json

# CSV export
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --format csv --output movers.csv
```

## Output

### Default Table Output

```
================================================================================
  MARKET MOVERS                                    Updated: 2025-01-14 15:30:00
================================================================================

  TOP GAINERS (24h)
--------------------------------------------------------------------------------
  Rank  Symbol      Price         Change    Vol Ratio   Market Cap    Score
--------------------------------------------------------------------------------
    1   XYZ       $1.234        +45.67%        5.2x      $123.4M      89.3
    2   ABC       $0.567        +32.10%        3.8x       $45.6M      76.5
    3   DEF       $2.890        +28.45%        2.9x      $234.5M      71.2
--------------------------------------------------------------------------------

  TOP LOSERS (24h)
--------------------------------------------------------------------------------
  Rank  Symbol      Price         Change    Vol Ratio   Market Cap    Score
--------------------------------------------------------------------------------
    1   GHI       $3.456        -28.90%        4.1x       $89.1M      72.1
    2   JKL       $0.123        -22.34%        2.5x       $12.3M      58.9
--------------------------------------------------------------------------------

  Summary: 42 movers found | Scanned: 1000 assets
================================================================================
```

### JSON Output (--format json)

```json
{
  "gainers": [
    {
      "rank": 1,
      "symbol": "XYZ",
      "name": "Example Token",
      "price": 1.234,
      "change_24h": 45.67,
      "volume_ratio": 5.2,
      "market_cap": 123400000,
      "significance_score": 89.3,
      "category": "defi"
    }
  ],
  "losers": [...],
  "meta": {
    "scan_time": "2025-01-14T15:30:00Z",
    "thresholds": {
      "min_change": 5,
      "volume_spike": 2,
      "min_market_cap": 10000000
    },
    "total_scanned": 1000,
    "matches": 42
  }
}
```

### Significance Score

The significance score (0-100) combines:
- **Change %** (40%): Larger moves score higher
- **Volume Ratio** (40%): Higher volume confirmation scores higher
- **Market Cap** (20%): Larger caps score slightly higher

Higher scores indicate more significant, higher-conviction moves.

## Configuration

Edit `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

```yaml
# Default Thresholds
thresholds:
  min_change: 5           # Minimum % change to include
  volume_spike: 2         # Minimum volume ratio (current/avg)
  min_market_cap: 10000000  # $10M minimum
  max_market_cap: null    # No maximum by default

# Scoring Weights
scoring:
  change_weight: 0.40
  volume_weight: 0.40
  cap_weight: 0.20

# Display
display:
  top_n: 20               # Number of results per category
  sort_by: significance   # significance, change, volume, market_cap

# Categories (CoinGecko category IDs)
categories:
  defi:
    - decentralized-finance-defi
    - yield-farming
  layer2:
    - layer-2
    - polygon-ecosystem
    - arbitrum-ecosystem
  nft:
    - non-fungible-tokens-nft
  gaming:
    - gaming
  meme:
    - meme-token
```

### Named Presets

Create presets in `${CLAUDE_SKILL_DIR}/config/presets/`:

**aggressive.yaml:**
```yaml
min_change: 3
volume_spike: 1.5
min_market_cap: 1000000
top_n: 50
```

**conservative.yaml:**
```yaml
min_change: 10
volume_spike: 3
min_market_cap: 100000000
top_n: 10
```

Use with:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --preset aggressive
```

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Dependency not found` | tracking-crypto-prices unavailable | Install market-price-tracker plugin |
| `No movers found` | Thresholds too strict | Relax thresholds with lower values |
| `Rate limit exceeded` | Too many API calls | Wait or use cached data |
| `Partial results` | Some assets unavailable | Normal, proceed with available data |

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed usage examples.

### Example 1: Daily Scan

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --timeframe 24h --top 20
```

### Example 2: Volume Spike Hunt

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --volume-spike 5 --min-volume 1000000
```

### Example 3: DeFi Movers Export

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --category defi --format csv --output defi_movers.csv
```

### Example 4: High-Cap Gainers

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-cap 1000000000 --gainers-only --top 10
```

## Integration with Other Skills

This skill can be combined with other crypto skills:

**With crypto-signal-generator:**
```bash
# Get movers, then generate signals for top gainers
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --format json | \
  python ../crypto-signal-generator/.../scanner.py --from-stdin
```

**With arbitrage-opportunity-finder:**
Volume spikes often precede arbitrage opportunities. Use movers as input for arbitrage scanning.

## Files

| File | Purpose |
|------|---------|
| `scripts/scanner.py` | Main CLI entry point |
| `scripts/analyzer.py` | Core analysis logic |
| `scripts/filters.py` | Threshold filtering |
| `scripts/scorers.py` | Significance scoring |
| `scripts/formatters.py` | Output formatting |
| `config/settings.yaml` | User configuration |
| `config/presets/` | Named preset configurations |

## Resources

- PRD.md - Product requirements
- ARD.md - Architecture documentation
- Depends on: tracking-crypto-prices skill
- CoinGecko API documentation: https://www.coingecko.com/en/api
