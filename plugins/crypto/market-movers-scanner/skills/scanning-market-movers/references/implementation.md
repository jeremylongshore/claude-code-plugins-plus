# Scanning Market Movers - Implementation Reference

## JSON Output Format

When using `--format json`, the scanner outputs:

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

## Significance Score

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

## Named Presets

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
