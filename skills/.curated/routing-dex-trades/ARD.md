# ARD: DEX Aggregator Router

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architectural Overview

### Pattern: Multi-Source Aggregation with Route Optimization

The DEX aggregator router follows a **fan-out/fan-in aggregation pattern** where multiple data sources are queried in parallel, results are normalized, and an optimization algorithm selects the best execution path.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DEX AGGREGATOR ROUTER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │   User      │───▶│   Router     │───▶│   Route Optimizer   │   │
│  │   Input     │    │   CLI        │    │                     │   │
│  └─────────────┘    └──────┬───────┘    └──────────┬──────────┘   │
│                            │                       │              │
│                            ▼                       ▼              │
│                   ┌────────────────┐    ┌─────────────────────┐   │
│                   │ Quote Fetcher  │    │   Split Calculator  │   │
│                   │ (Fan-Out)      │    │                     │   │
│                   └───────┬────────┘    └─────────────────────┘   │
│                           │                                       │
│         ┌─────────────────┼─────────────────┐                    │
│         ▼                 ▼                 ▼                    │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐               │
│  │  1inch     │   │  Paraswap  │   │  0x API    │               │
│  │  API       │   │  API       │   │            │               │
│  └────────────┘   └────────────┘   └────────────┘               │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           ▼                                       │
│                   ┌────────────────┐                             │
│                   │   Normalizer   │                             │
│                   │   & Ranker     │                             │
│                   └───────┬────────┘                             │
│                           │                                       │
│                           ▼                                       │
│                   ┌────────────────┐    ┌─────────────────────┐   │
│                   │   Formatter    │───▶│   Output            │   │
│                   │                │    │   (Table/JSON/CSV)  │   │
│                   └────────────────┘    └─────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow

1. **Input Parsing**: Validate token pair, amount, chain
2. **Fan-Out Queries**: Parallel requests to aggregator APIs
3. **Normalization**: Standardize quote formats across sources
4. **Route Discovery**: Identify direct, multi-hop, and split routes
5. **Optimization**: Rank routes by effective cost (price + gas + slippage)
6. **MEV Assessment**: Score routes for sandwich attack risk
7. **Output**: Present ranked recommendations with full cost breakdown

## Progressive Disclosure Strategy

### Level 1: Quick Quote (Default)

```bash
python dex_router.py ETH USDC 1.0
```

Output: Best price across aggregators with single recommended route.

### Level 2: Detailed Comparison

```bash
python dex_router.py ETH USDC 1.0 --compare
```

Output: All venues compared with price, gas, and effective rate.

### Level 3: Route Analysis

```bash
python dex_router.py ETH USDC 10.0 --routes
```

Output: Direct vs. multi-hop routes with hop-by-hop breakdown.

### Level 4: Split Optimization

```bash
python dex_router.py ETH USDC 100.0 --split
```

Output: Optimal split across DEXs with allocation percentages.

### Level 5: Full Analysis

```bash
python dex_router.py ETH USDC 50.0 --full --mev-check
```

Output: Complete analysis with MEV risk, gas optimization, all routes.

## Tool Permission Strategy

```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:dex-*)
```

### Rationale

- **Read/Write/Edit**: Configuration and output file management
- **Grep/Glob**: Search for token addresses and contract data
- **Bash(crypto:dex-*)**: Scoped to DEX-related scripts only

### Prohibited

- No unrestricted Bash (prevents arbitrary code execution)
- No network tools outside defined API clients
- No wallet/private key access

## Directory Structure

```
plugins/crypto/dex-aggregator-router/
├── .claude-plugin/
│   └── plugin.json
├── README.md
└── skills/
    └── routing-dex-trades/
        ├── PRD.md
        ├── ARD.md
        ├── SKILL.md
        ├── scripts/
        │   ├── dex_router.py          # Main CLI entry point
        │   ├── quote_fetcher.py       # Multi-API quote aggregation
        │   ├── route_optimizer.py     # Route ranking and selection
        │   ├── split_calculator.py    # Split order optimization
        │   ├── mev_assessor.py        # MEV risk scoring
        │   └── formatters.py          # Output formatting
        ├── references/
        │   ├── errors.md
        │   ├── examples.md
        │   └── implementation.md
        └── config/
            └── settings.yaml
```

## API Integration Architecture

### Multi-Source Quote Aggregation

```python
class QuoteFetcher:
    """Fan-out/fan-in quote aggregation from multiple sources."""

    AGGREGATORS = {
        "1inch": {
            "base_url": "https://api.1inch.dev/swap/v6.0",
            "chains": {1: "ethereum", 137: "polygon", 42161: "arbitrum"},
            "rate_limit": 1.0,  # requests per second
            "auth": "api_key"
        },
        "paraswap": {
            "base_url": "https://apiv5.paraswap.io",
            "chains": {1: 1, 137: 137, 42161: 42161},
            "rate_limit": 10.0,
            "auth": None
        },
        "0x": {
            "base_url": "https://api.0x.org/swap/v1",
            "chains": {1: "ethereum", 137: "polygon"},
            "rate_limit": 3.0,
            "auth": "api_key"
        }
    }

    async def fetch_all_quotes(self, params: SwapParams) -> List[Quote]:
        """Parallel fetch from all aggregators with timeout handling."""
        tasks = [
            self._fetch_with_timeout(agg, params)
            for agg in self.AGGREGATORS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._filter_valid_quotes(results)
```

### Quote Normalization

```python
@dataclass
class NormalizedQuote:
    """Standardized quote format across all sources."""
    source: str                    # Aggregator name
    input_token: str               # Input token address
    output_token: str              # Output token address
    input_amount: Decimal          # Input amount (wei)
    output_amount: Decimal         # Expected output (wei)
    price: Decimal                 # Price per token
    price_impact: float            # Percentage price impact
    gas_estimate: int              # Estimated gas units
    gas_price_gwei: float          # Current gas price
    gas_cost_usd: float            # Gas cost in USD
    effective_rate: Decimal        # Rate after gas costs
    route: List[str]               # Swap path (token addresses)
    route_readable: List[str]      # Swap path (symbols)
    protocols: List[str]           # DEXs used in route
    timestamp: datetime            # Quote timestamp
    valid_for_seconds: int         # Quote validity window
```

## Data Flow Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                 │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT                                                            │
│  ─────                                                            │
│  Token Pair: ETH → USDC                                          │
│  Amount: 10 ETH                                                   │
│  Chain: Ethereum (1)                                              │
│                                                                   │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    PARALLEL API CALLS                        │ │
│  │                                                              │ │
│  │  1inch ──────┐                                               │ │
│  │              │                                               │ │
│  │  Paraswap ───┼───▶ [Quote1, Quote2, Quote3, ...]            │ │
│  │              │                                               │ │
│  │  0x ─────────┘                                               │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    NORMALIZATION                             │ │
│  │                                                              │ │
│  │  • Convert to standard format                                │ │
│  │  • Calculate effective rates                                 │ │
│  │  • Add gas cost estimates                                    │ │
│  │  • Parse route details                                       │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    ROUTE OPTIMIZATION                        │ │
│  │                                                              │ │
│  │  Direct Routes:                                              │ │
│  │    ETH → USDC via Uniswap V3 (best liquidity)               │ │
│  │    ETH → USDC via Curve (lowest slippage)                   │ │
│  │                                                              │ │
│  │  Multi-Hop Routes:                                           │ │
│  │    ETH → WBTC → USDC (2 hops, lower impact)                 │ │
│  │    ETH → DAI → USDC (2 hops, stable pair)                   │ │
│  │                                                              │ │
│  │  Split Routes (for large trades):                            │ │
│  │    60% Uniswap V3 + 40% Curve                               │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    MEV ASSESSMENT                            │ │
│  │                                                              │ │
│  │  Risk Factors:                                               │ │
│  │    • Trade size vs. pool liquidity                          │ │
│  │    • Mempool visibility                                      │ │
│  │    • Route complexity                                        │ │
│  │                                                              │ │
│  │  Recommendations:                                            │ │
│  │    • Use Flashbots Protect for >$50K trades                 │ │
│  │    • Consider CoW Swap for MEV protection                   │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                                       │
│           ▼                                                       │
│  OUTPUT                                                           │
│  ──────                                                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  BEST ROUTE: 1inch via Uniswap V3                           │ │
│  │  ────────────────────────────────────────────────────────── │ │
│  │  Input:          10.0000 ETH                                │ │
│  │  Output:         25,432.18 USDC                             │ │
│  │  Rate:           2,543.218 USDC/ETH                         │ │
│  │  Price Impact:   0.12%                                      │ │
│  │  Gas Cost:       $8.45 (0.0032 ETH)                         │ │
│  │  Effective Rate: 2,542.37 USDC/ETH                          │ │
│  │  MEV Risk:       LOW                                        │ │
│  │  Valid For:      30 seconds                                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Error Handling Strategy

### Error Categories

| Category | Examples | Response |
|----------|----------|----------|
| API Timeout | Aggregator unresponsive | Use cached quote; warn staleness |
| Rate Limited | Too many requests | Exponential backoff; use alternative |
| Invalid Token | Unknown token address | Validate against token list |
| Insufficient Liquidity | No route found | Suggest alternative pairs |
| Quote Expired | Validity window passed | Auto-refresh with warning |
| Network Error | Chain RPC issues | Retry with fallback RPC |

### Graceful Degradation

```python
class QuoteFetcherWithFallback:
    """Resilient quote fetching with fallback chain."""

    async def get_best_quote(self, params: SwapParams) -> Optional[Quote]:
        # Try all aggregators in parallel
        quotes = await self.fetch_all_quotes(params)

        if quotes:
            return self.rank_quotes(quotes)[0]

        # Fallback: direct DEX subgraph queries
        subgraph_quotes = await self.fetch_from_subgraphs(params)

        if subgraph_quotes:
            return self.rank_quotes(subgraph_quotes)[0]

        # Final fallback: cached historical data
        return self.get_cached_estimate(params)
```

## Composability & Stacking

### Compatible Skills

| Skill | Integration | Data Flow |
|-------|-------------|-----------|
| gas-fee-optimizer | Gas price input | Receives current gas for calculations |
| arbitrage-opportunity-finder | Route sharing | Shares discovered routes for arb analysis |
| whale-alert-monitor | Trade size context | Large trade alerts inform split recommendations |
| flash-loan-simulator | Route composition | Routes can be components in flash loan paths |

### Stacking Example

```bash
# Combined workflow: Find arbitrage using optimal routes
python dex_router.py ETH USDC 50.0 --output-json routes.json
python arbitrage_finder.py --routes routes.json --check-profitability
```

## Performance & Scalability

### Caching Strategy

| Data Type | TTL | Storage |
|-----------|-----|---------|
| Token metadata | 24h | File cache |
| Gas prices | 15s | Memory |
| Quotes | 30s | Memory |
| Route paths | 5m | Memory |

### Concurrency

```python
# Parallel API calls with semaphore limiting
async def fetch_with_rate_limit(self, aggregators: List[str]):
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

    async with semaphore:
        tasks = [self._fetch_quote(agg) for agg in aggregators]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Total response time | <3s | End-to-end for full analysis |
| API fan-out | <1s | Parallel aggregator queries |
| Route optimization | <500ms | Algorithm processing |
| Memory usage | <100MB | Peak during operation |

## Testing Strategy

### Unit Tests

- Quote normalization for each aggregator format
- Route ranking algorithm correctness
- Split calculation math verification
- Gas cost calculations

### Integration Tests

- Live API connectivity (mocked in CI)
- Multi-aggregator response handling
- Error recovery scenarios

### Acceptance Tests

- Quote within 1% of manual check
- Route recommendations match expert analysis
- Split suggestions reduce simulated slippage

## Security & Compliance

### Data Handling

- No private keys or wallet access
- No transaction signing
- Read-only quote fetching
- API keys stored in environment variables

### Rate Limit Compliance

- Respect per-aggregator limits
- Implement exponential backoff
- Track usage across sessions

### Privacy

- No user tracking
- No trade logging beyond session
- No third-party data sharing

## Dependencies

### Python Packages

```
httpx>=0.24.0          # Async HTTP client
pydantic>=2.0          # Data validation
rich>=13.0             # Terminal formatting
asyncio                # Async/await support
```

### External Services

- 1inch API (optional API key)
- Paraswap API (no auth)
- 0x API (optional API key)
- Etherscan API (gas prices)
