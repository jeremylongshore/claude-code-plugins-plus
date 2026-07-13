# ARD: Crypto Derivatives Tracker

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Multi-Exchange Aggregation with Real-Time Processing**

This skill aggregates derivatives data from multiple exchanges, normalizes formats, and provides unified analysis across funding rates, open interest, liquidations, and options markets.

---

## Architectural Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    derivatives_tracker.py (CLI)                     │
│       funding | oi | liquidations | options | basis commands        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ FundingTracker  │    │   OIAnalyzer    │    │LiquidationMonitor│
│ Multi-exchange  │    │ Position data   │    │ Heatmap & alerts │
│ rate aggregation│    │ trend analysis  │    │ cascade risk     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │    ExchangeClient       │
                    │  Unified API interface  │
                    │  Rate limit handling    │
                    └─────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
    ┌─────────┐            ┌─────────┐            ┌─────────┐
    │ Binance │            │  Bybit  │            │ Deribit │
    │   API   │            │   API   │            │   API   │
    └─────────┘            └─────────┘            └─────────┘
```

---

## Workflow

### Step 1: Exchange Client Initialization

Configure API connections for each supported exchange with rate limiting.

### Step 2: Data Fetching

Parallel fetch from all exchanges for:

- Funding rates (perpetuals)
- Open interest (futures + perps)
- Recent liquidations
- Options data (Deribit primarily)

### Step 3: Data Normalization

Standardize formats across exchanges:

- Convert funding to 8-hour basis
- Normalize OI to USD equivalent
- Unify liquidation formats

### Step 4: Analysis & Aggregation

- Calculate weighted averages
- Detect divergences
- Generate signals

### Step 5: Output

Present in requested format (console/JSON).

---

## Data Flow

```
Exchange APIs          Normalization           Analysis              Output
┌───────────┐         ┌───────────┐         ┌───────────┐         ┌───────┐
│ Binance   │─────────│ Funding   │─────────│ Rate      │─────────│Console│
│ funding   │         │ Normalize │         │ Comparison│         │ JSON  │
└───────────┘         └───────────┘         └───────────┘         └───────┘
     │                      │                     │
┌───────────┐         ┌───────────┐         ┌───────────┐
│ Bybit     │─────────│ OI        │─────────│ Trend     │
│ OI data   │         │ Normalize │         │ Analysis  │
└───────────┘         └───────────┘         └───────────┘
     │                      │                     │
┌───────────┐         ┌───────────┐         ┌───────────┐
│ Deribit   │─────────│ Options   │─────────│ Flow      │
│ options   │         │ Normalize │         │ Analysis  │
└───────────┘         └───────────┘         └───────────┘
```

---

## Progressive Disclosure Strategy

### Level 1: Quick Summary

Single-line current funding rate or OI.

```
BTC Funding: +0.015% (Binance) | OI: $18.5B (+2.3% 24h)
```

### Level 2: Standard Report

Tabular view across exchanges with key metrics.

```
BTC FUNDING RATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exchange    Current    24h Avg    Annualized
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Binance     +0.0150%   +0.0120%   +16.43%
Bybit       +0.0180%   +0.0140%   +19.71%
...
```

### Level 3: Deep Analysis

Full derivatives dashboard with all metrics, signals, and risk assessment.

---

## Tool Permission Strategy

```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:derivatives-*)
```

### Tool Justification

| Tool | Usage |
|------|-------|
| Read | Load config, API credentials |
| Write | Save reports, cache data |
| Edit | Update configuration |
| Grep | Search historical data |
| Glob | Find data files |
| Bash(crypto:derivatives-*) | Execute data fetching scripts |

---

## Directory Structure

```
skills/tracking-crypto-derivatives/
├── SKILL.md                     # Core skill instructions
├── PRD.md                       # Product requirements
├── ARD.md                       # This file
├── scripts/
│   ├── derivatives_tracker.py   # Main CLI entry point
│   ├── exchange_client.py       # Unified exchange interface
│   ├── funding_tracker.py       # Funding rate analysis
│   ├── oi_analyzer.py           # Open interest analysis
│   ├── liquidation_monitor.py   # Liquidation tracking
│   ├── options_analyzer.py      # Options market analysis
│   ├── basis_calculator.py      # Basis/arbitrage calculations
│   └── formatters.py            # Output formatting
├── config/
│   └── settings.yaml            # Exchange configs, thresholds
└── references/
    ├── errors.md                # Error handling guide
    ├── examples.md              # Usage examples
    └── implementation.md        # Implementation details
```

---

## API Integration Architecture

### Exchange Client Interface

```python
class ExchangeClient:
    """Unified interface for all exchanges."""

    def get_funding_rate(self, symbol: str) -> FundingRate
    def get_open_interest(self, symbol: str) -> OpenInterest
    def get_liquidations(self, symbol: str, limit: int) -> List[Liquidation]
    def get_options_data(self, symbol: str) -> OptionsData
```

### Supported Exchanges

| Exchange | Funding | OI | Liquidations | Options |
|----------|---------|-------|--------------|---------|
| Binance  | ✓ | ✓ | ✓ | ✗ |
| Bybit    | ✓ | ✓ | ✓ | ✓ |
| OKX      | ✓ | ✓ | ✓ | ✓ |
| Deribit  | ✓ | ✓ | ✗ | ✓ (primary) |
| BitMEX   | ✓ | ✓ | ✓ | ✗ |

### Rate Limiting Strategy

```python
RATE_LIMITS = {
    "binance": {"requests_per_minute": 1200, "weight_per_request": 1},
    "bybit": {"requests_per_minute": 120, "weight_per_request": 1},
    "okx": {"requests_per_minute": 60, "weight_per_request": 1},
    "deribit": {"requests_per_day": 10000, "weight_per_request": 1},
}
```

---

## Data Models

### FundingRate

```python
@dataclass
class FundingRate:
    exchange: str
    symbol: str
    rate: Decimal           # Current 8-hour rate
    predicted_rate: Decimal # Next predicted rate
    next_payment: datetime  # Time until next payment
    annualized: float       # Annualized yield
```

### OpenInterest

```python
@dataclass
class OpenInterest:
    exchange: str
    symbol: str
    oi_usd: Decimal         # Total OI in USD
    oi_contracts: Decimal   # Total contracts
    change_24h_pct: float   # 24h change
    change_7d_pct: float    # 7d change
    long_ratio: float       # Long/short ratio
```

### Liquidation

```python
@dataclass
class Liquidation:
    exchange: str
    symbol: str
    side: str               # "long" or "short"
    price: Decimal
    quantity: Decimal
    value_usd: Decimal
    timestamp: datetime
```

### OptionsSnapshot

```python
@dataclass
class OptionsSnapshot:
    symbol: str
    expiry: date
    atm_iv: float           # At-the-money IV
    put_call_ratio: float   # By volume
    put_call_oi: float      # By open interest
    max_pain: Decimal       # Max pain price
    total_oi_usd: Decimal
```

---

## Error Handling Strategy

### Exchange Errors

| Error Type | Handling |
|------------|----------|
| API Rate Limit | Exponential backoff, queue requests |
| API Timeout | Retry with fallback exchange |
| Invalid Symbol | Skip exchange, continue others |
| Auth Failed | Log warning, use public endpoints |

### Data Quality

| Issue | Handling |
|-------|----------|
| Stale Data | Flag staleness, show warning |
| Missing Exchange | Exclude from aggregation |
| Inconsistent Units | Normalize to standard format |

---

## Composability & Stacking

### Works With

| Skill | Integration |
|-------|-------------|
| market-price-tracker | Spot price for basis calculations |
| arbitrage-finder | Cross-exchange funding arbitrage |
| options-flow-analyzer | Deep options analysis |
| whale-alert-monitor | Large liquidation correlation |

### Output Formats

- **Console**: Formatted tables and reports
- **JSON**: Machine-readable for pipelines
- **CSV**: Export for spreadsheet analysis

---

## Performance & Scalability

### Caching Strategy

```python
CACHE_TTL = {
    "funding_rates": 60,      # 1 minute
    "open_interest": 30,      # 30 seconds
    "liquidations": 10,       # 10 seconds
    "options_data": 300,      # 5 minutes
}
```

### Parallel Fetching

```python
async def fetch_all_funding(symbols: List[str]) -> Dict[str, FundingRate]:
    """Fetch funding from all exchanges in parallel."""
    tasks = [
        fetch_funding(exchange, symbol)
        for exchange in EXCHANGES
        for symbol in symbols
    ]
    return await asyncio.gather(*tasks)
```

---

## Testing Strategy

### Unit Tests

- Funding rate calculations
- OI normalization
- Liquidation aggregation
- Basis calculations

### Integration Tests

- Exchange API connectivity
- Rate limit handling
- Error recovery

### Mock Data

- Simulated exchange responses
- Historical liquidation data
- Options chain snapshots

---

## Security & Compliance

### API Key Handling

- Keys stored in environment variables or config
- Read-only permissions only (no trading)
- No key logging in outputs

### Data Privacy

- No personal data collected
- No trading history stored
- Analysis only, no execution

---

## Monitoring & Alerts

### Alert Thresholds (Configurable)

```yaml
alerts:
  funding_extreme: 0.1      # 0.1% 8-hour funding
  oi_change_large: 15       # 15% OI change
  liquidation_large: 1000000 # $1M liquidation
  iv_extreme: 100           # 100% IV
```

### Alert Outputs

- Console warnings with emoji indicators
- JSON alerts for webhook integration
- Summary at end of report
