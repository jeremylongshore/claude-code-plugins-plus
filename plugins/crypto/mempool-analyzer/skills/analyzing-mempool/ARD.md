# ARD: Mempool Analyzer

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Stream Processing Pattern** - Python CLI that subscribes to mempool updates, decodes transactions, and presents analyzed data.

## Workflow

```
RPC Connection → Mempool Subscription → TX Decode → Analysis → Output
      ↓               ↓                    ↓           ↓         ↓
  WebSocket      newPendingTx          ABI Decode   Classify    Table/JSON
```

## Data Flow

```
Input: RPC URL, filters (contract, method, min_value)
          ↓
Subscription: eth_subscribe("newPendingTransactions")
          ↓
Fetch: eth_getTransactionByHash for each pending tx
          ↓
Decode: Parse input data using known ABIs
          ↓
Analyze: Classify (swap, transfer, approval), estimate value
          ↓
Output: Formatted display or JSON stream
```

## Directory Structure

```
skills/analyzing-mempool/
├── PRD.md                    # This requirements doc
├── ARD.md                    # This architecture doc
├── SKILL.md                  # Agent instructions
├── scripts/
│   ├── mempool_analyzer.py   # Main CLI entry point
│   ├── rpc_client.py         # Ethereum RPC/WebSocket client
│   ├── tx_decoder.py         # Transaction decoding
│   ├── gas_analyzer.py       # Gas price analysis
│   ├── mev_detector.py       # MEV opportunity detection
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   └── examples.md           # Usage examples
└── config/
    └── settings.yaml         # Default configuration
```

## API Integration

### Ethereum RPC

- **Endpoints**: `eth_pendingTransactions`, `eth_getTransactionByHash`, `eth_gasPrice`
- **Auth**: RPC URL with API key embedded
- **WebSocket**: `eth_subscribe` for real-time updates

### Transaction Decoding

- **Router ABIs**: Uniswap V2/V3, SushiSwap, 1inch
- **Method Detection**: Swap, addLiquidity, removeLiquidity, approve
- **Value Estimation**: Using pool reserves or price feeds

## Component Design

### rpc_client.py

```python
class MempoolClient:
    def connect(rpc_url) -> None
    def get_pending_transactions(limit) -> List[PendingTx]
    def subscribe_pending(callback) -> None
    def get_gas_price() -> GasInfo
```

### tx_decoder.py

```python
class TransactionDecoder:
    def decode_input(tx) -> DecodedCall
    def identify_dex_swap(tx) -> Optional[SwapInfo]
    def estimate_usd_value(tx) -> float
```

### gas_analyzer.py

```python
class GasAnalyzer:
    def analyze_pending_gas() -> GasDistribution
    def recommend_gas(priority) -> GasRecommendation
    def estimate_inclusion_time(gas_price) -> int
```

### mev_detector.py

```python
class MEVDetector:
    def detect_sandwich_opportunity(pending_txs) -> List[Opportunity]
    def detect_arbitrage(pending_swaps) -> List[Opportunity]
    def detect_liquidation(pending_txs) -> List[Opportunity]
```

## Error Handling Strategy

| Error | Handling |
|-------|----------|
| RPC connection failed | Retry with backoff, show connection status |
| WebSocket disconnected | Auto-reconnect with exponential backoff |
| ABI decode failed | Label as "Unknown" with raw data |
| Rate limit | Queue requests, show warning |
| Invalid transaction | Skip with warning, continue stream |

## Gas Analysis Algorithm

```
1. Fetch last N blocks gas prices
2. Fetch pending tx gas prices
3. Calculate percentiles (10th, 25th, 50th, 75th, 90th)
4. Recommend based on urgency:
   - Slow: 10th percentile (may take 10+ blocks)
   - Standard: 50th percentile (2-5 blocks)
   - Fast: 75th percentile (1-2 blocks)
   - Instant: 90th percentile (next block likely)
```

## DEX Detection

Supported routers with ABI decoding:

- Uniswap V2 Router
- Uniswap V3 Router
- SushiSwap Router
- Curve pools
- Balancer pools
- 1inch Aggregator

## Performance Considerations

- WebSocket preferred over HTTP polling
- Batch RPC calls where possible
- Cache decoded ABIs
- Limit pending tx fetch to reasonable count (100-500)
- Stream mode for continuous monitoring

## Security

- No private keys required (read-only)
- RPC URL may contain API key (handle securely)
- No transaction submission capability
