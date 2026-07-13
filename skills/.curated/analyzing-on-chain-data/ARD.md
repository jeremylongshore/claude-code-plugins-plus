# ARD: On-Chain Analytics

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architectural Overview

### Pattern

Data Aggregation with Multi-Source Normalization

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request                                 │
│    "analyze defi tvl", "compare protocol revenue", "top dapps"  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   onchain_analytics.py                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐ │
│  │ tvl_cmd    │ │ revenue_cmd│ │ users_cmd  │ │ compare_cmd  │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     data_fetcher.py                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Multi-source aggregation with caching and normalization     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │ DeFiLlama │   │  Token    │   │ CoinGecko │
       │    API    │   │ Terminal  │   │    API    │
       └───────────┘   └───────────┘   └───────────┘
```

### Workflow

1. Parse user query (TVL, revenue, users, comparison)
2. Route to appropriate data fetcher
3. Aggregate data from multiple sources
4. Normalize and calculate derived metrics
5. Format and display results

## Progressive Disclosure Strategy

| Level | Content | Location |
|-------|---------|----------|
| L1: Quick Start | CLI examples, common queries | SKILL.md |
| L2: Configuration | API setup, defaults | config/settings.yaml |
| L3: Implementation | Data normalization, caching | references/implementation.md |
| L4: Advanced | Custom metrics, API queries | references/examples.md |

## Directory Structure

```
skills/analyzing-on-chain-data/
├── SKILL.md                    # Core instructions
├── PRD.md                      # Product requirements
├── ARD.md                      # Architecture (this file)
├── scripts/
│   ├── onchain_analytics.py    # Main CLI
│   ├── data_fetcher.py         # Multi-source data fetching
│   ├── metrics_calculator.py   # Derived metrics calculation
│   └── formatters.py           # Output formatting
├── references/
│   ├── errors.md               # Error handling
│   ├── examples.md             # Usage examples
│   └── implementation.md       # Implementation details
└── config/
    └── settings.yaml           # Configuration
```

## API Integration Architecture

### DeFiLlama (Primary - No Rate Limits)

```python
# Protocol TVL
GET /protocols

# Chain TVL
GET /v2/chains

# Protocol Revenue/Fees
GET /overview/fees/{protocol}

# Historical TVL
GET /protocol/{protocol}
```

### Token Terminal (Secondary)

```python
# Protocol metrics
GET /v2/protocols/{protocol}

# Market data
GET /v2/metrics/market_data
```

## Data Flow Architecture

```
Input: "top defi protocols by tvl"
         │
         ▼
┌─────────────────────────┐
│   Parse Query           │
│   - Metric: TVL         │
│   - Filter: DeFi        │
│   - Sort: descending    │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Fetch Data            │
│   - DeFiLlama protocols │
│   - Cache check         │
│   - Rate limit handling │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Calculate Metrics     │
│   - Market share        │
│   - Growth rates        │
│   - Rankings            │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Format Output         │
│   - Table / JSON / CSV  │
│   - Charts if requested │
└─────────────────────────┘
```

## Error Handling Strategy

| Error | Cause | Recovery |
|-------|-------|----------|
| API unavailable | Service down | Use cached data, try backup |
| Rate limited | Too many requests | Exponential backoff |
| Missing protocol | Not in database | Suggest alternatives |
| Invalid date range | Future or malformed | Validate and suggest fix |

## Caching Strategy

- **Protocol list**: TTL 1 hour
- **TVL data**: TTL 5 minutes
- **Revenue data**: TTL 15 minutes (updates daily)
- **Historical data**: TTL 24 hours (immutable)
- **User metrics**: TTL 30 minutes

## Security Considerations

- API keys stored in environment variables
- No user data or private information
- Rate limit compliance
- Input validation for all parameters
