# ARD: Market Price Tracker

**Version**: 2.0.0
**Author**: Jeremy Longshore <jeremy@intentsolutions.io>
**Status**: In Development
**Last Updated**: 2025-01-14

---

## Document Control

| Field | Value |
|-------|-------|
| **Skill Name** | tracking-crypto-prices |
| **Architectural Pattern** | Read-Process-Write with Caching |
| **Complexity Level** | Medium (4 steps) |
| **API Integrations** | 2 (CoinGecko, yfinance) |
| **Token Budget** | ~2,500 tokens / 5,000 max |
| **Status** | In Development |
| **Owner** | Jeremy Longshore |

---

## 1. Architectural Overview

### 1.1 Skill Purpose

**One-Sentence Summary**: Fetch, cache, and present cryptocurrency price data from multiple sources with standardized output for both human consumption and programmatic use by dependent skills.

**Architectural Pattern**: Read-Process-Write with Caching

**Why This Pattern**:
- **Read**: Fetch price data from external APIs
- **Cache**: Store recently fetched data to reduce API calls
- **Process**: Normalize data from different sources into standard format
- **Write**: Output to terminal (human) or files (programmatic)

This pattern suits the foundation skill nature - it must be fast, reliable, and provide a consistent interface for 10+ dependent skills.

### 1.2 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MARKET PRICE TRACKER                            │
│                   Foundation Skill Architecture                       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  USER INPUT   │          │   CACHE       │          │  DEPENDENT    │
│  - Symbol     │          │   LAYER       │          │  SKILLS       │
│  - Watchlist  │          │   (30s TTL)   │          │  (via import) │
│  - Period     │          │               │          │               │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────┐
         │  Step 1: VALIDATE INPUT                      │
         │  ├─ Parse symbol/name                        │
         │  ├─ Resolve aliases (BTC → bitcoin)          │
         │  └─ Output: Normalized symbol list           │
         └─────────────────────────────────────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────┐
         │  Step 2: CHECK CACHE                         │
         │  ├─ Load cache from data/cache.json          │
         │  ├─ Check TTL (30s for spot, 1h for OHLCV)   │
         │  └─ Output: Cached data OR cache miss        │
         └─────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │ Cache Hit?                  │
                    ├─────────────────────────────┤
                    │ YES: Skip to Step 4         │
                    │ NO:  Continue to Step 3     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────┐
         │  Step 3: FETCH FROM API                      │
         │  ├─ Primary: CoinGecko /simple/price         │
         │  ├─ Fallback: yfinance (if CoinGecko fails)  │
         │  ├─ Retry with exponential backoff           │
         │  └─ Output: Raw price data (JSON)            │
         └─────────────────────────────────────────────┘
                                   │
                                   ▼
         ┌─────────────────────────────────────────────┐
         │  Step 4: PROCESS & OUTPUT                    │
         │  ├─ Normalize to standard schema             │
         │  ├─ Update cache                             │
         │  ├─ Format for human (table) or machine      │
         │  └─ Output: Formatted response OR JSON file  │
         └─────────────────────────────────────────────┘
```

### 1.3 Workflow Summary

**Total Steps**: 4

| Step | Action | Type | Dependencies | Output |
|------|--------|------|--------------|--------|
| 1 | Validate Input | Code | None | Normalized symbols |
| 2 | Check Cache | Code | data/cache.json | Cached data or miss |
| 3 | Fetch from API | API Call | CoinGecko/yfinance | Raw JSON |
| 4 | Process & Output | Code | Step 2 or 3 output | Formatted response |

---

## 2. Progressive Disclosure Strategy

### 2.1 Level 1: Frontmatter (Metadata)

**What Goes Here**: ONLY `name` and `description`

```yaml
---
name: tracking-crypto-prices
description: |
  Track real-time cryptocurrency prices across exchanges with historical data and alerts.
  Provides price data infrastructure for dependent skills (portfolio, tax, DeFi, arbitrage).
  Use when checking crypto prices, monitoring markets, or fetching historical data.
  Trigger with phrases like "check price", "BTC price", "crypto prices", "price history",
  "get quote for", "what's ETH trading at", or "show me the top 10 prices".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
```

**Description Quality Target**: 85%+
**Character Count**: 445 characters (within 500 limit for extended description)

### 2.2 Level 2: SKILL.md (Core Instructions)

**Token Budget**: ~2,500 tokens (target <500 lines)

**Required Sections**:
1. Overview (what + who uses this)
2. Prerequisites (pip install)
3. Instructions (4 numbered steps with code)
4. Output (example formats)
5. Configuration (settings.yaml reference)
6. Error Handling (common errors + solutions)
7. Composability (how to use with other skills)
8. Examples (3 concrete use cases)

### 2.3 Level 3: Resources (Extended Context)

**scripts/ Directory**:
```
scripts/
├── price_tracker.py      # Main entry point (CLI)
├── api_client.py         # CoinGecko/yfinance abstraction
├── cache_manager.py      # Cache read/write/invalidation
└── formatters.py         # Human-readable output formatting
```

**references/ Directory**:
```
references/
├── errors.md             # Common errors and solutions
├── examples.md           # Extended use cases
└── implementation.md     # Technical deep-dive
```

**config/ Directory**:
```
config/
└── settings.yaml         # API keys, cache duration, watchlists
```

---

## 3. Tool Permission Strategy

### 3.1 Required Tools

**Minimal Necessary Set**:
- `Read` - Load cache, read config files
- `Write` - Save cache, export CSV/JSON
- `Bash(python:*)` - Execute Python scripts

### 3.2 Tool Usage Justification

| Tool | Why Needed | Usage Pattern |
|------|------------|---------------|
| Read | Load cached prices, read settings | Steps 2, 4 |
| Write | Save cache, export historical data | Steps 3, 4 |
| Bash(python:*) | Execute price fetching scripts | All steps |

### 3.3 Tools Explicitly NOT Needed

**Excluded Tools**:
- `Edit` - Scripts generate fresh output, no editing required
- `WebFetch` - Python scripts handle HTTP directly via requests
- `Grep` - No code search needed for price queries
- `Glob` - No file pattern matching needed

---

## 4. Directory Structure & File Organization

### 4.1 Complete Skill Structure

```
plugins/crypto/market-price-tracker/skills/tracking-crypto-prices/
├── PRD.md                          # Product Requirements Document
├── ARD.md                          # Architecture Requirements Document (this file)
├── SKILL.md                        # Core instructions (<500 lines)
│
├── scripts/                        # Executable code
│   ├── price_tracker.py            # Main CLI entry point
│   ├── api_client.py               # API abstraction layer
│   ├── cache_manager.py            # Caching logic
│   └── formatters.py               # Output formatting
│
├── references/                     # Documentation
│   ├── errors.md                   # Error handling guide
│   ├── examples.md                 # Extended examples
│   └── implementation.md           # Technical details
│
├── config/                         # Configuration
│   └── settings.yaml               # User-configurable settings
│
└── data/                           # Runtime data (gitignored)
    ├── cache.json                  # Price cache
    └── *.csv                       # Exported historical data
```

### 4.2 File Naming Conventions

**Scripts**: `[noun]_[purpose].py`
- ✅ `price_tracker.py` - Main price tracking logic
- ✅ `api_client.py` - API communication
- ✅ `cache_manager.py` - Cache operations

**References**: `[purpose].md` (lowercase)
- ✅ `errors.md` - Error documentation
- ✅ `examples.md` - Usage examples

### 4.3 Path Referencing Standard

**Always Use**: `${CLAUDE_SKILL_DIR}` for all file paths in SKILL.md

```bash
# Correct
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC

# Incorrect
python scripts/price_tracker.py --symbol BTC  # Missing ${CLAUDE_SKILL_DIR}
```

---

## 5. API Integration Architecture

### 5.1 External API Integrations

**API 1: CoinGecko (Primary)**

**Purpose**: Real-time price data for 10,000+ cryptocurrencies

**Integration Details**:
- **Base URL**: `https://api.coingecko.com/api/v3`
- **Authentication**: Optional API key (header: `x-cg-demo-api-key` or `x-cg-pro-api-key`)
- **Rate Limits**: 10-30 calls/minute (free), 500/minute (Pro)
- **Response Format**: JSON

**Endpoints Used**:

| Endpoint | Purpose | Rate Impact |
|----------|---------|-------------|
| `/simple/price` | Current prices (batch) | 1 call per request |
| `/coins/{id}` | Detailed coin data | 1 call per coin |
| `/coins/{id}/market_chart` | Historical OHLCV | 1 call per coin/range |
| `/coins/markets` | Top coins by market cap | 1 call per page |

**Example Request**:
```python
import requests

def get_prices(symbols: list, vs_currency: str = "usd") -> dict:
    """Fetch current prices for multiple symbols."""
    ids = ",".join(symbols)
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ids,
        "vs_currencies": vs_currency,
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true"
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()
```

**Example Response**:
```json
{
  "bitcoin": {
    "usd": 97234.56,
    "usd_24h_change": 2.34,
    "usd_24h_vol": 28500000000,
    "usd_market_cap": 1920000000000
  },
  "ethereum": {
    "usd": 3456.78,
    "usd_24h_change": 1.87,
    "usd_24h_vol": 12300000000,
    "usd_market_cap": 415200000000
  }
}
```

**Error Handling**:
| Code | Cause | Solution |
|------|-------|----------|
| 429 | Rate limit exceeded | Exponential backoff (1s, 2s, 4s, 8s) |
| 404 | Unknown coin ID | Return error with suggestion |
| 500 | Server error | Retry 3x, then fallback to yfinance |

---

**API 2: yfinance (Fallback)**

**Purpose**: Backup price source, primary for historical OHLCV data

**Integration Details**:
- **Library**: `yfinance` Python package
- **Authentication**: None required
- **Rate Limits**: Implicit (respectful usage)
- **Response Format**: pandas DataFrame

**Example Usage**:
```python
import yfinance as yf

def get_historical(symbol: str, period: str = "30d") -> pd.DataFrame:
    """Fetch historical OHLCV data."""
    ticker = yf.Ticker(f"{symbol}-USD")
    df = ticker.history(period=period, interval="1d")
    df.columns = [c.lower() for c in df.columns]
    return df
```

**Symbol Mapping**:
- CoinGecko uses full names: `bitcoin`, `ethereum`
- yfinance uses tickers: `BTC-USD`, `ETH-USD`
- api_client.py handles translation

### 5.2 API Call Sequencing

```
User Request
    │
    ▼
Check Cache (local, fast)
    │
    ├── Cache HIT ────────────────────────────────────────┐
    │                                                      │
    ▼ Cache MISS                                          │
    │                                                      │
Try CoinGecko API                                         │
    │                                                      │
    ├── Success ──────────────────────────┐               │
    │                                      │               │
    ▼ Failure (429/500)                   │               │
    │                                      │               │
Fallback to yfinance                      │               │
    │                                      │               │
    ├── Success ─────────────────┐        │               │
    │                             │        │               │
    ▼ Failure                    │        │               │
    │                             │        │               │
Return Cached (stale) + Warning  │        │               │
    │                             │        │               │
    └─────────────────────────────┴────────┴───────────────┘
                                  │
                                  ▼
                          Update Cache
                                  │
                                  ▼
                          Format & Return
```

**Fallback Strategy**:
1. CoinGecko (primary) → yfinance (fallback) → Cache (stale, last resort)
2. Always return *something* - stale data with warning beats error

---

## 6. Data Flow Architecture

### 6.1 Input → Processing → Output Pipeline

```
INPUT (User Request: "BTC price")
    │
    ▼
Step 1: Parse & Validate
    │   Input: "BTC" (string)
    │   Processing: Resolve to CoinGecko ID "bitcoin"
    │   Output: {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"}
    │
    ▼
Step 2: Check Cache
    │   Input: Cache key "bitcoin_usd_spot"
    │   Processing: Load data/cache.json, check TTL
    │   Output: Cached price data OR cache miss flag
    │
    ▼
Step 3: Fetch (if cache miss)
    │   Input: Symbol ID "bitcoin"
    │   API Call: CoinGecko /simple/price
    │   Processing: Parse JSON, handle errors
    │   Output: {"price": 97234.56, "change_24h": 2.34, ...}
    │
    ▼
Step 4: Format & Return
    │   Input: Price data dict
    │   Processing: Update cache, format output
    │   Output: Human-readable table OR JSON file
    │
    ▼
FINAL OUTPUT
```

### 6.2 Data Format Specifications

**Format 1: Cache Entry** (`data/cache.json`)
```json
{
  "bitcoin_usd_spot": {
    "symbol": "BTC",
    "name": "Bitcoin",
    "price": 97234.56,
    "change_24h": 2.34,
    "volume_24h": 28500000000,
    "market_cap": 1920000000000,
    "currency": "usd",
    "fetched_at": "2025-01-14T15:30:00Z",
    "ttl_seconds": 30
  }
}
```

**Format 2: Standardized Price Output** (returned to dependent skills)
```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  "price": 97234.56,
  "currency": "USD",
  "change_24h_percent": 2.34,
  "volume_24h": 28500000000,
  "market_cap": 1920000000000,
  "timestamp": "2025-01-14T15:30:00Z",
  "source": "coingecko",
  "cached": false
}
```

**Format 3: Historical OHLCV** (`data/BTC_30d.csv`)
```csv
date,open,high,low,close,volume
2024-12-15,95000.00,96500.00,94200.00,96100.00,25000000000
2024-12-16,96100.00,97800.00,95800.00,97500.00,27000000000
...
```

### 6.3 Data Validation Rules

**Validation Checkpoints**:

1. **Input Validation** (Step 1):
   - ✅ Symbol is string, 1-10 characters
   - ✅ Symbol resolves to known cryptocurrency
   - ✅ Currency is supported (USD, EUR, GBP, etc.)

2. **Cache Validation** (Step 2):
   - ✅ Cache file exists and is valid JSON
   - ✅ Entry TTL not exceeded
   - ✅ Required fields present

3. **API Response Validation** (Step 3):
   - ✅ HTTP 200 status
   - ✅ JSON parseable
   - ✅ Price is positive number
   - ✅ Required fields present

---

## 7. Error Handling Strategy

### 7.1 Error Categories & Responses

**Category 1: Input Errors**

| Error | Cause | Detection | Solution |
|-------|-------|-----------|----------|
| Unknown symbol | User typed invalid ticker | Symbol lookup fails | Suggest similar symbols |
| Invalid currency | Unsupported fiat currency | Currency not in list | Show supported currencies |
| Empty input | No symbols provided | Input validation | Show usage example |

**Category 2: API Errors**

| Error | Cause | Detection | Solution |
|-------|-------|-----------|----------|
| Rate limited (429) | Too many requests | HTTP status | Exponential backoff + retry |
| Server error (500) | CoinGecko down | HTTP status | Fallback to yfinance |
| Timeout | Slow network | Exception | Retry with longer timeout |
| Auth failed (401) | Invalid API key | HTTP status | Check config, use free tier |

**Category 3: Cache Errors**

| Error | Cause | Detection | Solution |
|-------|-------|-----------|----------|
| Cache corrupted | Invalid JSON | Parse exception | Delete cache, refetch |
| Cache missing | First run or deleted | File not found | Create empty cache |
| Cache stale | TTL exceeded | Timestamp check | Refetch from API |

### 7.2 Graceful Degradation

```
Primary Path:
  CoinGecko API → Cache → Format → User
            ↓ (if API fails)
Fallback Path 1:
  yfinance → Cache → Format → User
            ↓ (if yfinance fails)
Fallback Path 2:
  Stale Cache → Format → User (with warning)
            ↓ (if no cache)
Error Path:
  Clear error message + suggested action
```

### 7.3 Logging Format

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [Component] Message
[2025-01-14 15:30:00] [INFO] [API] Fetching BTC price from CoinGecko
[2025-01-14 15:30:01] [INFO] [API] ✓ Got price: $97,234.56
[2025-01-14 15:30:01] [INFO] [Cache] Updated bitcoin_usd_spot (TTL: 30s)
[2025-01-14 15:30:45] [WARN] [API] Rate limited (429), backing off 2s
[2025-01-14 15:30:47] [INFO] [API] Retry successful
```

---

## 8. Composability & Stacking Architecture

### 8.1 Standalone Execution

This skill can run independently for direct user queries:

```bash
# Single price
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC

# Multiple prices
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbols BTC,ETH,SOL

# Historical data
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --period 30d --output csv
```

### 8.2 Skill Stacking Patterns

**Pattern 1: Direct Import (Preferred for Python skills)**

Other skills import price_tracker functions directly:

```python
# In crypto-portfolio-tracker/scripts/portfolio.py
import sys
sys.path.insert(0, "${CLAUDE_SKILL_DIR}/../market-price-tracker/skills/tracking-crypto-prices/scripts")
from price_tracker import get_current_prices

def calculate_portfolio_value(holdings: dict) -> float:
    """Value portfolio using price tracker."""
    prices = get_current_prices(list(holdings.keys()))
    total = sum(holdings[sym] * prices[sym]["price"] for sym in holdings)
    return total
```

**Pattern 2: CLI Subprocess (Cross-language or isolation)**

```bash
# In another skill's script
PRICES=$(python ${CLAUDE_SKILL_DIR}/../market-price-tracker/scripts/price_tracker.py \
  --symbols BTC,ETH \
  --format json)
```

**Pattern 3: Shared Cache (Efficient for batch operations)**

Multiple skills read from the same cache file:
- price-tracker updates `data/cache.json`
- portfolio-tracker reads from same cache
- Reduces redundant API calls

### 8.3 Skills That Depend on This

| Skill | Integration Pattern | Data Needed |
|-------|---------------------|-------------|
| market-movers-scanner | Direct import | Batch prices + 24h change |
| crypto-portfolio-tracker | Direct import | Current prices for holdings |
| crypto-tax-calculator | Direct import | Historical prices for cost basis |
| defi-yield-optimizer | CLI subprocess | USD prices for APY calculation |
| liquidity-pool-analyzer | Direct import | Token prices for LP valuation |
| staking-rewards-optimizer | CLI subprocess | Token prices for rewards calc |
| crypto-derivatives-tracker | Direct import | Underlying asset prices |
| dex-aggregator-router | Direct import | CEX prices for comparison |
| options-flow-analyzer | Direct import | Underlying prices |
| arbitrage-opportunity-finder | Direct import | Multi-exchange prices |

### 8.4 Input/Output Contracts

**Input Contract** (what this skill expects):
```python
# Function signature for get_current_prices()
def get_current_prices(
    symbols: list[str],           # Required: ["BTC", "ETH"]
    currency: str = "usd",        # Optional: Default USD
    use_cache: bool = True,       # Optional: Default True
    cache_ttl: int = 30           # Optional: Seconds
) -> dict[str, PriceData]:
    ...
```

**Output Contract** (what this skill guarantees):
```python
@dataclass
class PriceData:
    symbol: str           # "BTC"
    name: str             # "Bitcoin"
    price: float          # 97234.56
    currency: str         # "USD"
    change_24h: float     # 2.34 (percent)
    volume_24h: float     # 28500000000
    market_cap: float     # 1920000000000
    timestamp: str        # ISO 8601
    source: str           # "coingecko" or "yfinance"
    cached: bool          # True if from cache
```

---

## 9. Performance & Scalability

### 9.1 Performance Targets

| Metric | Target | Max Acceptable | Notes |
|--------|--------|----------------|-------|
| Single price (cached) | < 100ms | < 500ms | Local file read only |
| Single price (API) | < 2s | < 5s | Network dependent |
| Batch 10 prices (API) | < 3s | < 8s | Single API call |
| Batch 50 prices (API) | < 5s | < 15s | May require pagination |
| Historical 30d OHLCV | < 3s | < 10s | yfinance call |

### 9.2 Scalability Considerations

**Cache Strategy**:
- Spot prices: 30s TTL (balance freshness vs rate limits)
- Historical data: 1h TTL (rarely changes)
- Cache file: Single JSON file (sufficient for <1000 entries)

**Batch Optimization**:
- CoinGecko supports 100+ coins per request
- Always batch multiple symbol requests
- Single API call vs N calls = 100x reduction

### 9.3 Resource Usage

**Disk**: ~1MB for cache + historical exports
**Memory**: ~50MB during execution
**Network**: ~10KB per API request

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Test Input Validation**:
```python
def test_symbol_resolution():
    assert resolve_symbol("BTC") == "bitcoin"
    assert resolve_symbol("btc") == "bitcoin"
    assert resolve_symbol("Bitcoin") == "bitcoin"
    assert resolve_symbol("INVALID") is None
```

**Test Cache**:
```python
def test_cache_hit():
    cache.set("bitcoin", price_data, ttl=30)
    result = cache.get("bitcoin")
    assert result is not None
    assert result["cached"] is True

def test_cache_miss():
    cache.clear()
    result = cache.get("bitcoin")
    assert result is None
```

### 10.2 Integration Tests

```bash
# Test full workflow
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --test

# Expected: Fetches real data, validates response format
```

### 10.3 Acceptance Criteria

- [ ] Single price returns in < 3s
- [ ] Batch 10 prices returns in < 5s
- [ ] Cache reduces repeat queries to < 100ms
- [ ] Fallback to yfinance works when CoinGecko fails
- [ ] Historical data exports valid CSV
- [ ] All error cases return helpful messages

---

## 11. Security & Compliance

### 11.1 API Key Management

**Storage**: Environment variables or `config/settings.yaml`

```yaml
# config/settings.yaml
api:
  coingecko:
    api_key: ${COINGECKO_API_KEY}  # From environment
    use_pro: false
```

**Never**:
- Hardcode API keys in scripts
- Commit API keys to git
- Log API keys

### 11.2 Data Privacy

**User Data**: No PII collected
**Market Data**: Public information, no privacy concerns
**Cache**: Local only, user can delete anytime

### 11.3 Rate Limit Compliance

- Respect CoinGecko rate limits (10-50/min free tier)
- Implement exponential backoff
- Use caching aggressively

---

## 12. Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-01 | Initial stub | Jeremy Longshore |
| 2.0.0 | 2025-01-14 | Full ARD per nixtla standard | Jeremy Longshore |

---

## 13. Approval

| Role | Name | Approval Date |
|------|------|---------------|
| Architect | Claude (Opus 4.5) | 2025-01-14 |
| Owner | Jeremy Longshore | 2025-01-14 |

---

**Document maintained by**: Intent Solutions
**Standard**: Nixtla Enterprise Skill ARD Template v1.0
