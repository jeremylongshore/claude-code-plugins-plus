# ARD: Scanning Market Movers

## Document Control

| Field | Value |
|-------|-------|
| Skill Name | scanning-market-movers |
| Architecture Pattern | Analysis Pipeline with Dependency Injection |
| Version | 2.0.0 |
| Author | Jeremy Longshore <jeremy@intentsolutions.io> |
| Created | 2025-01-14 |
| Updated | 2025-01-14 |

---

## Architectural Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request                                 │
│  "Scan for top gainers with > 3x volume spike in DeFi"          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCANNER.PY (Main Entry)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Parse     │─▶│   Load      │─▶│   Invoke    │             │
│  │   Args      │  │   Config    │  │   Analyzer  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYZER.PY (Core Logic)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 1: Fetch Market Data                               │     │
│  │  ┌─────────────────────────────────────────────────┐   │     │
│  │  │  DEPENDENCY: tracking-crypto-prices             │   │     │
│  │  │  - get_all_prices() → current prices + 24h vol │   │     │
│  │  │  - Leverages existing cache infrastructure      │   │     │
│  │  └─────────────────────────────────────────────────┘   │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 2: Calculate Metrics                               │     │
│  │  - Price change % (1h, 24h, 7d)                        │     │
│  │  - Volume ratio (current / avg)                        │     │
│  │  - Significance score (weighted composite)             │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 3: Apply Filters                                   │     │
│  │  - Change % threshold                                  │     │
│  │  - Volume spike threshold                              │     │
│  │  - Market cap range                                    │     │
│  │  - Category filter                                     │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Step 4: Rank & Sort                                     │     │
│  │  - Sort by significance score (default)                │     │
│  │  - Or by change %, volume, market cap                  │     │
│  │  - Limit to top N results                              │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FORMATTERS.PY (Output)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Table     │  │    JSON     │  │    CSV      │             │
│  │   Format    │  │   Format    │  │   Format    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Pattern

**Analysis Pipeline with Dependency Injection**

This skill follows a pipeline pattern where market data flows through sequential processing stages. The price data infrastructure is injected from the `tracking-crypto-prices` dependency, avoiding code duplication and ensuring consistent caching behavior.

### Workflow Summary

| Step | Component | Function |
|------|-----------|----------|
| 1 | Parse Arguments | Validate user input, load presets |
| 2 | Fetch Data | Get prices/volumes from tracking-crypto-prices |
| 3 | Calculate Metrics | Compute changes, ratios, scores |
| 4 | Filter Results | Apply user-defined thresholds |
| 5 | Rank & Output | Sort, limit, and format results |

---

## Progressive Disclosure Strategy

### Level 1: Quick Scan (Beginner)

**Command:**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py
```

**What happens:**
- Uses default thresholds (5% change, 2x volume, $10M+ market cap)
- Returns top 20 gainers and top 20 losers
- Table output with essential columns

**User learns:**
- Basic scanner invocation
- Default output format

### Level 2: Custom Thresholds (Intermediate)

**Command:**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-change 10 --volume-spike 3x --top 50
```

**What happens:**
- User customizes thresholds
- More selective filtering
- Larger result set

**User learns:**
- Threshold configuration
- Result set control

### Level 3: Full Configuration (Advanced)

**Command:**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py \
  --preset aggressive \
  --category defi \
  --sort-by significance \
  --format json \
  --output movers.json
```

**What happens:**
- Named preset for common configurations
- Category filtering for sector focus
- Custom sort criteria
- Export to file

**User learns:**
- Preset system
- Category filtering
- Export workflows

---

## Tool Permission Strategy

### Allowed Tools

```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*)
```

### Tool Usage Matrix

| Tool | Purpose | Security Consideration |
|------|---------|----------------------|
| Read | Load config, access cache | Read-only access to config files |
| Write | Export results | Only writes to user-specified paths |
| Edit | Not typically used | Available for config modification |
| Grep | Search log files | For debugging/troubleshooting |
| Glob | Find cache files | Directory listing |
| Bash(python:*) | Execute scanner scripts | Sandboxed to Python execution |

### Security Boundaries

- Scripts only access local filesystem for cache and config
- No network access except through tracking-crypto-prices dependency
- No execution of arbitrary code
- Output paths validated before writing

---

## Directory Structure

```
plugins/crypto/market-movers-scanner/skills/scanning-market-movers/
├── PRD.md                    # Product requirements
├── ARD.md                    # Architecture (this file)
├── SKILL.md                  # Core instructions
├── scripts/
│   ├── scanner.py            # Main CLI entry point
│   ├── analyzer.py           # Core analysis logic
│   ├── filters.py            # Threshold filtering
│   ├── scorers.py            # Significance scoring
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   ├── examples.md           # Usage examples
│   └── implementation.md     # Implementation details
├── config/
│   ├── settings.yaml         # Main configuration
│   └── presets/              # Named presets
│       ├── aggressive.yaml   # High-threshold preset
│       └── conservative.yaml # Low-threshold preset
└── data/
    └── categories.json       # Asset category mappings
```

---

## Dependency Integration

### Primary Dependency: tracking-crypto-prices

The scanner relies on `tracking-crypto-prices` for all market data. This avoids duplicating API integration logic and ensures consistent caching.

#### Integration Pattern: Direct Import

```python
# In analyzer.py
import sys
sys.path.insert(0, str(PRICE_TRACKER_PATH / "scripts"))

from api_client import CryptoAPIClient
from cache_manager import CacheManager

def get_market_data():
    """Fetch market data using tracking-crypto-prices infrastructure."""
    client = CryptoAPIClient()
    cache = CacheManager()

    # Get all prices (leverages existing cache)
    all_coins = client.list_coins()
    prices = []

    for coin in all_coins[:1000]:  # Top 1000 by market cap
        try:
            price = client.get_current_price(coin['id'])
            prices.append(price)
        except APIError:
            continue  # Skip unavailable coins

    return prices
```

#### Integration Pattern: CLI Subprocess (Alternative)

```python
import subprocess
import json

def get_prices_via_cli(symbols):
    """Get prices via CLI for isolation."""
    result = subprocess.run([
        'python', str(PRICE_TRACKER_PATH / 'scripts' / 'price_tracker.py'),
        '--symbols', ','.join(symbols),
        '--format', 'json'
    ], capture_output=True, text=True)

    return json.loads(result.stdout)
```

#### Dependency Path Resolution

```python
from pathlib import Path

# Resolve dependency path relative to plugin root
PLUGIN_ROOT = Path(__file__).parent.parent.parent.parent
PRICE_TRACKER_PATH = PLUGIN_ROOT.parent / 'market-price-tracker' / 'skills' / 'tracking-crypto-prices'

# Verify dependency exists
if not (PRICE_TRACKER_PATH / 'scripts' / 'price_tracker.py').exists():
    raise ImportError("tracking-crypto-prices dependency not found")
```

---

## Data Flow Architecture

### Input Data

| Source | Data | Update Frequency |
|--------|------|------------------|
| tracking-crypto-prices | Current prices, 24h change, volume, market cap | Cached 30s |
| CoinGecko | Category metadata | Cached 1 hour |
| User config | Thresholds, presets | On change |

### Internal Data Flow

```
┌──────────────────┐
│ Raw Price Data   │
│ (from dependency)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Calculated       │
│ Metrics          │
│ - change_pct     │
│ - volume_ratio   │
│ - significance   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Filtered Set     │
│ (threshold       │
│ matching)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Ranked Results   │
│ (sorted, limited)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Formatted Output │
│ (table/json/csv) │
└──────────────────┘
```

### Output Formats

#### Table Format

```
================================================================================
  MARKET MOVERS                                    Updated: 2025-01-14 15:30:00
================================================================================

  TOP GAINERS (24h)
--------------------------------------------------------------------------------
  Symbol      Price        Change      Volume Ratio    Market Cap    Score
--------------------------------------------------------------------------------
  XYZ       $1.234        +45.67%          5.2x         $123.4M       89.3
  ABC       $0.567        +32.10%          3.8x          $45.6M       76.5
--------------------------------------------------------------------------------

  TOP LOSERS (24h)
--------------------------------------------------------------------------------
  Symbol      Price        Change      Volume Ratio    Market Cap    Score
--------------------------------------------------------------------------------
  DEF       $2.345        -23.45%          4.1x          $89.1M       72.1
--------------------------------------------------------------------------------
```

#### JSON Format

```json
{
  "gainers": [
    {
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

---

## Error Handling Strategy

### Error Categories

| Category | Example | Handling |
|----------|---------|----------|
| Dependency Error | tracking-crypto-prices unavailable | Clear error message, suggest installation |
| Data Error | No price data returned | Graceful degradation, partial results |
| Config Error | Invalid threshold value | Validate on load, use defaults |
| Filter Error | No results match criteria | Suggest relaxed thresholds |

### Error Fallback Hierarchy

```
1. Primary: Direct import from tracking-crypto-prices
     ↓ (ImportError)
2. Fallback: CLI subprocess call
     ↓ (subprocess failure)
3. Last Resort: Cached data (if available)
     ↓ (no cache)
4. Error: Clear message with remediation steps
```

### User-Friendly Error Messages

```python
ERROR_MESSAGES = {
    "dependency_missing": """
        Error: tracking-crypto-prices skill not found.

        This skill depends on market-price-tracker plugin.
        Ensure it's installed and the path is correct.

        Expected path: {expected_path}
    """,
    "no_results": """
        No market movers found matching your criteria.

        Current thresholds:
        - Minimum change: {min_change}%
        - Volume spike: {volume_spike}x
        - Minimum market cap: ${min_cap}

        Try relaxing thresholds with:
          --min-change 3 --volume-spike 1.5
    """,
    "api_error": """
        Warning: Some price data unavailable.

        Partial results shown ({available}/{total} assets).
        This may be due to API rate limits or connectivity.
    """
}
```

---

## Significance Scoring Algorithm

### Default Scoring Formula

```
Score = (W1 × ChangeScore) + (W2 × VolumeScore) + (W3 × CapScore)

Where:
  W1 = 0.40 (change weight)
  W2 = 0.40 (volume weight)
  W3 = 0.20 (market cap weight)

ChangeScore = min(100, |change_pct| × 2)
VolumeScore = min(100, volume_ratio × 20)
CapScore = min(100, log10(market_cap) × 10)
```

### Implementation

```python
def calculate_significance(change_pct, volume_ratio, market_cap, weights=None):
    """Calculate significance score for ranking movers."""
    weights = weights or {'change': 0.40, 'volume': 0.40, 'cap': 0.20}

    # Normalize change (cap at 100)
    change_score = min(100, abs(change_pct) * 2)

    # Normalize volume ratio (cap at 100)
    volume_score = min(100, volume_ratio * 20)

    # Normalize market cap (log scale)
    import math
    cap_score = min(100, math.log10(max(market_cap, 1)) * 10)

    # Weighted sum
    score = (
        weights['change'] * change_score +
        weights['volume'] * volume_score +
        weights['cap'] * cap_score
    )

    return round(score, 1)
```

---

## Performance Considerations

### Scan Optimization

| Technique | Benefit |
|-----------|---------|
| Leverage dependency cache | Avoid redundant API calls |
| Early filtering | Process only relevant assets |
| Batch processing | Minimize loop overhead |
| Lazy loading | Only fetch needed data |

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Full scan (1000 assets) | < 5 seconds | With warm cache |
| Cold start | < 15 seconds | First run, empty cache |
| Memory usage | < 100 MB | For 10,000 asset scan |

---

## Testing Strategy

### Unit Tests

```python
def test_significance_scoring():
    """Test significance score calculation."""
    # High change, high volume, high cap
    score = calculate_significance(50, 5, 1_000_000_000)
    assert 80 <= score <= 100

    # Low change, low volume, low cap
    score = calculate_significance(1, 1, 1_000_000)
    assert 0 <= score <= 30

def test_filtering():
    """Test threshold filtering."""
    movers = [
        {'change_24h': 10, 'volume_ratio': 3, 'market_cap': 100_000_000},
        {'change_24h': 3, 'volume_ratio': 1, 'market_cap': 50_000_000},
    ]

    filtered = apply_filters(movers, min_change=5, volume_spike=2)
    assert len(filtered) == 1
```

### Integration Tests

```python
def test_dependency_integration():
    """Test tracking-crypto-prices integration."""
    from analyzer import get_market_data

    data = get_market_data()
    assert len(data) > 0
    assert 'price' in data[0]
    assert 'volume_24h' in data[0]
```

---

## Security & Compliance

### Security Measures

- No credential storage in code
- Read-only access to dependency cache
- Validated output paths
- No arbitrary code execution

### Compliance Notes

- Price data is sourced from public APIs
- No personal data collected or stored
- Results are ephemeral (not persisted)
- Scanner does not constitute financial advice

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-10-20 | Auto-generated | Initial stub |
| 2.0.0 | 2025-01-14 | Jeremy Longshore | Full ARD with architecture |
