# ARD: Cross-Chain Bridge Monitor

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Data Aggregation Pattern** - Python CLI that aggregates bridge data from multiple APIs and on-chain sources for unified monitoring.

## Workflow

```
Data Fetch → Aggregation → Analysis → Display
    ↓            ↓           ↓          ↓
DefiLlama    Normalize    Compare    Table/Alert
Protocols    by Chain     Routes
```

## Data Flow

```
Input: Bridge query (TVL, liquidity, transaction, compare)
          ↓
API Fetch: DefiLlama + protocol-specific endpoints
          ↓
Aggregate: Combine data from multiple sources
          ↓
Analyze: Calculate fees, times, risk metrics
          ↓
Output: Formatted tables, JSON, or alerts
```

## Directory Structure

```
skills/monitoring-cross-chain-bridges/
├── PRD.md                    # Product requirements
├── ARD.md                    # Architecture document
├── SKILL.md                  # Agent instructions
├── scripts/
│   ├── bridge_monitor.py     # Main CLI entry point
│   ├── bridge_fetcher.py     # API client for bridge data
│   ├── protocol_adapters.py  # Protocol-specific adapters
│   ├── tx_tracker.py         # Transaction status tracking
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   └── examples.md           # Usage examples
└── config/
    └── settings.yaml         # Default configuration
```

## API Integration

### DefiLlama Bridges API

- **Endpoint**: `https://bridges.llama.fi/`
- **Endpoints**:
  - `/bridges` - List all bridges with TVL
  - `/bridge/{id}` - Bridge details
  - `/bridgevolume/{chain}` - Volume by chain
  - `/bridgedaystats/{timestamp}/{chain}` - Historical stats
- **Rate Limits**: Public API, fair use

### Bridge Protocol APIs

- **Wormhole**: `https://api.wormholescan.io/`
- **LayerZero**: `https://layerzeroscan.com/api/`
- **Stargate**: `https://api.stargate.finance/`
- **Across**: `https://across.to/api/`
- **Hop**: `https://hop.exchange/api/`

### On-Chain Verification

- Use RPC calls to verify bridge contract balances
- Track pending transactions via tx hash

## Component Design

### bridge_monitor.py

```python
# Main CLI with commands:
# - tvl: Show bridge TVL rankings
# - liquidity: Check liquidity by chain/token
# - tx: Track transaction status
# - compare: Compare routes between chains
# - chains: List supported chains
# - bridges: List supported bridges
```

### bridge_fetcher.py

```python
class BridgeFetcher:
    def get_all_bridges() -> List[BridgeInfo]
    def get_bridge_tvl(bridge_id: str) -> TVLData
    def get_chain_volume(chain: str) -> VolumeData
    def get_bridge_volume(bridge_id: str, days: int) -> List[VolumeDay]
```

### protocol_adapters.py

```python
class ProtocolAdapter:
    def get_supported_chains() -> List[str]
    def get_liquidity(chain: str, token: str) -> Decimal
    def get_fee_estimate(src: str, dst: str, amount: Decimal) -> FeeEstimate
    def get_tx_status(tx_hash: str) -> TxStatus
```

### tx_tracker.py

```python
class TxTracker:
    def track_bridge_tx(tx_hash: str, bridge: str) -> TxStatus
    def get_pending_txs(address: str) -> List[PendingTx]
    def verify_on_chain(chain: str, tx_hash: str) -> bool
```

## Data Structures

### BridgeInfo

```python
@dataclass
class BridgeInfo:
    id: str
    name: str
    display_name: str
    icon: str
    volume_prev_day: float
    volume_prev2_day: float
    chains: List[str]
    destination_chains: List[str]
```

### TVLData

```python
@dataclass
class TVLData:
    bridge_id: str
    total_tvl: float
    tvl_by_chain: Dict[str, float]
    tvl_by_token: Dict[str, float]
    last_updated: datetime
```

### TxStatus

```python
@dataclass
class TxStatus:
    tx_hash: str
    bridge: str
    source_chain: str
    dest_chain: str
    status: str  # pending, confirmed, completed, failed
    source_confirmed: bool
    dest_confirmed: bool
    amount: Decimal
    token: str
    timestamp: int
    estimated_completion: Optional[int]
```

### FeeEstimate

```python
@dataclass
class FeeEstimate:
    bridge: str
    source_chain: str
    dest_chain: str
    token: str
    amount: Decimal
    bridge_fee: Decimal
    gas_fee_source: Decimal
    gas_fee_dest: Decimal
    total_fee: Decimal
    estimated_time_minutes: int
```

## Supported Bridges

| Bridge | Type | Chains | API |
|--------|------|--------|-----|
| Wormhole | Messaging | 20+ | REST |
| LayerZero | Messaging | 50+ | REST |
| Stargate | Liquidity | 10+ | REST |
| Across | Liquidity | 10+ | REST |
| Hop | Liquidity | 6 | REST |
| Celer | Liquidity | 15+ | REST |
| Synapse | Liquidity | 15+ | REST |
| Multichain | Lock/Mint | 60+ | REST |

## Error Handling Strategy

| Error | Handling |
|-------|----------|
| API unavailable | Fallback to cached data |
| Rate limited | Exponential backoff |
| Invalid bridge | Show supported bridges |
| Tx not found | Retry with delay |
| Chain not supported | Show supported chains |

## Performance Considerations

- Cache TVL data (5 minute TTL)
- Cache bridge list (1 hour TTL)
- Parallel API calls for comparisons
- Lazy load protocol adapters
- Rate limit per-API

## Security

- Read-only operations
- No wallet connections
- No transaction signing
- Public API endpoints only
- No sensitive data storage
