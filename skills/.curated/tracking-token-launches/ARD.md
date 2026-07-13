# ARD: Token Launch Tracker

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Event Streaming Pattern** - Python CLI that monitors blockchain events and aggregates data from multiple sources.

## Workflow

```
Event Detection → Data Enrichment → Risk Analysis → Display
       ↓                ↓                ↓            ↓
  RPC/Websocket    Token Info        Contract      Table/Alert
                                     Analysis
```

## Data Flow

```
Input: Chain selection + filters (time, DEX, liquidity)
          ↓
Monitor: PairCreated events from DEX factories
          ↓
Enrich: Fetch token metadata (name, symbol, supply)
          ↓
Analyze: Check contract for red flags
          ↓
Filter: Apply user criteria (min liquidity, etc.)
          ↓
Output: Formatted launch list with risk indicators
```

## Directory Structure

```
skills/tracking-token-launches/
├── PRD.md                    # Product requirements
├── ARD.md                    # Architecture document
├── SKILL.md                  # Agent instructions
├── scripts/
│   ├── launch_tracker.py     # Main CLI entry point
│   ├── event_monitor.py      # Blockchain event listener
│   ├── token_analyzer.py     # Token contract analysis
│   ├── dex_sources.py        # DEX factory addresses
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   └── examples.md           # Usage examples
└── config/
    └── settings.yaml         # Default configuration
```

## API Integration

### Ethereum RPC (eth_getLogs)

- **Events**: PairCreated, Transfer, Mint
- **Data**: New pair address, token addresses, reserves

### DexScreener API

- **Endpoint**: `https://api.dexscreener.com/latest/dex/tokens/{address}`
- **Data**: Price, liquidity, volume, pair info

### GeckoTerminal API

- **Endpoint**: `https://api.geckoterminal.com/api/v2/`
- **Data**: New pools, token info, trading data

## Component Design

### event_monitor.py

```python
class EventMonitor:
    def get_recent_pairs(chain, dex, hours) -> List[PairCreated]
    def stream_new_pairs(chain, callback) -> None
    def get_liquidity_adds(pair_address) -> List[LiquidityEvent]
```

### token_analyzer.py

```python
class TokenAnalyzer:
    def get_token_info(address) -> TokenInfo
    def check_contract(address) -> ContractAnalysis
    def get_holders(address, top_n) -> List[Holder]
    def detect_honeypot(address) -> HoneypotResult
```

### dex_sources.py

```python
# DEX factory addresses per chain
DEX_FACTORIES = {
    "ethereum": {
        "uniswap_v2": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "uniswap_v3": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "sushiswap": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
    },
    # ... more chains
}
```

## Data Structures

### PairCreated Event

```python
@dataclass
class PairCreated:
    block_number: int
    timestamp: int
    pair_address: str
    token0: str
    token1: str
    dex: str
    chain: str
```

### TokenInfo

```python
@dataclass
class TokenInfo:
    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: int
    owner: str
    is_verified: bool
```

### ContractAnalysis

```python
@dataclass
class ContractAnalysis:
    has_mint_function: bool
    has_blacklist: bool
    is_proxy: bool
    ownership_renounced: bool
    liquidity_locked: bool
    risk_score: int  # 0-100
```

## Risk Indicators

| Indicator | Risk Level | Detection |
|-----------|------------|-----------|
| Mint function | High | Bytecode analysis |
| Blacklist/whitelist | Medium | Function signature |
| Not verified | Medium | Block explorer API |
| Proxy contract | Medium | Implementation check |
| Owner not renounced | Low | owner() call |
| Low initial liquidity | Warning | Reserve check |
| Few holders | Warning | Holder count |

## Supported Chains

| Chain | Chain ID | DEXes |
|-------|----------|-------|
| Ethereum | 1 | Uniswap V2/V3, Sushiswap |
| BSC | 56 | PancakeSwap V2/V3 |
| Arbitrum | 42161 | Camelot, Uniswap |
| Base | 8453 | Aerodrome, Uniswap |
| Polygon | 137 | QuickSwap, Uniswap |

## Error Handling Strategy

| Error | Handling |
|-------|----------|
| RPC connection failed | Fallback to backup RPC |
| Rate limited | Exponential backoff |
| Contract not verified | Show warning, limited analysis |
| Invalid chain | Return supported chains list |

## Performance Considerations

- Cache token info (24h TTL)
- Batch RPC calls when possible
- Use websockets for real-time monitoring
- Limit historical scan to 24h default

## Security

- No wallet connections
- Read-only operations
- API keys in environment variables
- No transaction signing
