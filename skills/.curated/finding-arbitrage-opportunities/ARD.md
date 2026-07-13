# ARD: Finding Arbitrage Opportunities

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Pattern**: Multi-Source Aggregation + Graph Analysis

This skill aggregates price data from multiple sources (CEX APIs, DEX subgraphs, on-chain oracles) and applies graph algorithms to detect arbitrage paths. The architecture separates data fetching, opportunity detection, and profit calculation into independent components.

## Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARBITRAGE OPPORTUNITY FINDER                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   CEX APIs   │    │ DEX Subgraph │    │  On-Chain    │          │
│  │   (CCXT)     │    │  (GraphQL)   │    │  (RPC)       │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│         └───────────────────┼───────────────────┘                   │
│                             ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   PRICE AGGREGATOR                           │   │
│  │  • Normalize formats (bid/ask/mid)                          │   │
│  │  • Timestamp validation                                      │   │
│  │  • Source reliability scoring                                │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                        │
│         ┌───────────────────┼───────────────────┐                   │
│         ▼                   ▼                   ▼                   │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐              │
│  │   Direct   │     │ Triangular │     │   Cross-   │              │
│  │  Scanner   │     │  Finder    │     │   Chain    │              │
│  └─────┬──────┘     └─────┬──────┘     └─────┬──────┘              │
│        │                  │                  │                      │
│        └──────────────────┼──────────────────┘                      │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  PROFIT CALCULATOR                           │   │
│  │  • Trading fees (maker/taker)                               │   │
│  │  • Swap fees (DEX-specific)                                 │   │
│  │  • Gas costs (network-specific)                             │   │
│  │  • Slippage estimates (size-based)                          │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   OPPORTUNITY RANKER                         │   │
│  │  • Net profit calculation                                    │   │
│  │  • Risk scoring                                              │   │
│  │  • Execution complexity                                      │   │
│  │  • Time sensitivity                                          │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                        │
│                             ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      OUTPUT                                  │   │
│  │  • Console tables with color-coded profits                  │   │
│  │  • JSON for bot integration                                 │   │
│  │  • Alerts for threshold breaches                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

### Level 1: Quick Scan (Default)

- Single pair, top exchanges
- Basic spread display
- Simple profit estimate

### Level 2: Detailed Analysis (`--detailed`)

- All available exchanges
- Fee breakdown
- Slippage estimates
- Risk indicators

### Level 3: Full Discovery (`--full`)

- Triangular path discovery
- Cross-chain comparison
- Historical spread context
- Execution recommendations

## Tool Permission Strategy

```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:arbitrage-*)

# Scoped bash for:
# - arbitrage-scan: Run opportunity scanner
# - arbitrage-monitor: Real-time monitoring
# - arbitrage-calc: Profit calculations
```

## Directory Structure

```
plugins/crypto/arbitrage-opportunity-finder/
├── skills/
│   └── finding-arbitrage-opportunities/
│       ├── SKILL.md                    # Core instructions
│       ├── PRD.md                      # Product requirements
│       ├── ARD.md                      # Architecture (this file)
│       ├── scripts/
│       │   ├── arb_finder.py           # Main CLI entry point
│       │   ├── price_fetcher.py        # Multi-source price aggregation
│       │   ├── opportunity_scanner.py  # Direct spread detection
│       │   ├── triangular_finder.py    # Graph-based path finder
│       │   ├── profit_calculator.py    # Cost-aware profit calculation
│       │   └── formatters.py           # Output formatting
│       ├── config/
│       │   └── settings.yaml           # Exchange and API config
│       └── references/
│           ├── errors.md               # Error handling
│           └── examples.md             # Usage examples
```

## API Integration Architecture

### Price Data Sources

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCE HIERARCHY                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRIMARY: Direct Exchange APIs (via CCXT)                       │
│  ├── Binance, Coinbase, Kraken, KuCoin, OKX                    │
│  ├── Real-time order book data                                  │
│  └── Lowest latency, highest accuracy                           │
│                                                                  │
│  SECONDARY: DEX Subgraphs (GraphQL)                             │
│  ├── Uniswap, SushiSwap, Curve, Balancer                       │
│  ├── Pool reserve data for price calculation                    │
│  └── ~1-3 second latency                                        │
│                                                                  │
│  TERTIARY: Aggregators (REST)                                   │
│  ├── CoinGecko, CoinMarketCap                                  │
│  ├── Pre-aggregated prices (may be delayed)                     │
│  └── Good for overview, not precision trading                   │
│                                                                  │
│  FALLBACK: On-Chain Oracles                                     │
│  ├── Chainlink price feeds                                      │
│  └── Most reliable but least granular                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Fee Structure Database

| Venue Type | Fee Model | Typical Range |
|------------|-----------|---------------|
| CEX (Spot) | Maker/Taker | 0.02% - 0.10% |
| Uniswap V3 | Pool Fee | 0.01% - 1.00% |
| SushiSwap | Fixed | 0.30% |
| Curve | Dynamic | 0.01% - 0.04% |
| Balancer | Pool-specific | 0.01% - 10% |

## Data Flow Architecture

### Input Processing

```
User Request
    │
    ▼
┌─────────────────────┐
│  Parse Arguments    │
│  • token_pair       │
│  • exchanges        │
│  • threshold        │
│  • mode             │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Validate Inputs    │
│  • Token exists     │
│  • Exchange valid   │
│  • Threshold range  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Load Config        │
│  • API endpoints    │
│  • Fee schedules    │
│  • Gas prices       │
└─────────────────────┘
```

### Opportunity Detection

```
Price Data
    │
    ▼
┌─────────────────────┐
│  Build Price Matrix │
│  exchange × pair    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Calculate Spreads  │
│  buy_price[A] vs    │
│  sell_price[B]      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Apply Costs        │
│  - Trading fees     │
│  - Withdrawal fees  │
│  - Gas (if DEX)     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Filter & Rank      │
│  profit > threshold │
└─────────────────────┘
```

## Error Handling Strategy

| Error Type | Detection | Response |
|------------|-----------|----------|
| API Rate Limit | HTTP 429 | Exponential backoff, switch source |
| Stale Data | Timestamp > 10s | Warning, mark unreliable |
| Exchange Offline | Connection timeout | Skip, use alternatives |
| Invalid Pair | No price data | Log, suggest alternatives |
| Slippage Exceeded | Size > liquidity | Reduce size or flag |

## Composability & Stacking

### Standalone Use

```bash
python arb_finder.py scan ETH USDC --exchanges binance,coinbase,kraken
```

### Pipeline Integration

```bash
python arb_finder.py scan ETH USDC --output json | jq '.opportunities[0]'
```

### With Flash Loan Simulator

```bash
# Find opportunity, then simulate flash loan execution
python arb_finder.py scan ETH USDC --output json | \
  python ../flash-loan-simulator/scripts/flash_simulator.py arbitrage --stdin
```

### Continuous Monitoring

```bash
python arb_finder.py monitor ETH USDC --threshold 0.5 --interval 5
```

## Performance & Scalability

### Latency Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Single exchange fetch | < 500ms | Direct API |
| Multi-exchange scan (5) | < 2s | Parallel requests |
| Triangular path (100 pairs) | < 3s | Graph algorithm |
| Full scan (all exchanges) | < 10s | Rate-limited |

### Optimization Strategies

1. **Parallel Fetching**: Concurrent API calls to multiple exchanges
2. **Caching**: Short-lived cache (5s) for repeated queries
3. **Incremental Updates**: Only re-fetch changed prices in monitor mode
4. **Graph Pruning**: Exclude low-liquidity pairs from triangular search

## Security & Compliance

### API Key Handling

- Keys loaded from environment variables or encrypted config
- Never logged or displayed in output
- Rate limits respected to avoid bans

### Data Privacy

- No user data collected or stored
- Price data is public market information
- No personally identifiable information

### Risk Warnings

- All opportunities marked as estimates
- Execution risk disclaimers
- Educational purpose disclaimer

## Testing Strategy

### Unit Tests

- Price normalization
- Fee calculations
- Spread computations
- Path finding algorithms

### Integration Tests

- API connectivity (with mocks)
- Multi-source aggregation
- End-to-end opportunity detection

### Manual Validation

- Compare detected spreads with exchange UIs
- Verify profit calculations with manual trades
- Test rate limit handling
