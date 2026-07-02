# ARD: Gas Fee Optimizer

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Analytics Pipeline Pattern** - Python CLI that fetches gas data, analyzes patterns, and provides optimization recommendations.

## Workflow

```
Data Collection → Analysis → Recommendation → Display
      ↓             ↓            ↓              ↓
  RPC + APIs    Historical   Timing/Price     Table/JSON
```

## Data Flow

```
Input: User request (current gas, optimal time, estimate for operation)
          ↓
Fetch: Multiple gas oracles (Etherscan Gas Oracle, RPC eth_feeHistory)
          ↓
Aggregate: Combine sources, calculate percentiles
          ↓
Analyze: Compare to historical patterns
          ↓
Recommend: Optimal timing, price recommendation
          ↓
Output: Formatted results with USD costs
```

## Directory Structure

```
skills/optimizing-gas-fees/
├── PRD.md                    # This requirements doc
├── ARD.md                    # This architecture doc
├── SKILL.md                  # Agent instructions
├── scripts/
│   ├── gas_optimizer.py      # Main CLI entry point
│   ├── gas_fetcher.py        # Multi-source gas data
│   ├── pattern_analyzer.py   # Historical pattern detection
│   ├── cost_estimator.py     # Transaction cost estimation
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   └── examples.md           # Usage examples
└── config/
    └── settings.yaml         # Default configuration
```

## API Integration

### Ethereum RPC

- **Method**: `eth_gasPrice`, `eth_feeHistory`
- **Data**: Current gas price, base fee history

### Etherscan Gas Oracle (Primary)

- **Endpoint**: `https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=<ETHERSCAN_API_KEY>`
- **Auth**: free API key via the `ETHERSCAN_API_KEY` environment variable
- **Rate limit**: 5 calls/sec on the free tier — cache responses (see Performance Considerations)
- **Data**: `SafeGasPrice` / `ProposeGasPrice` / `FastGasPrice` (gwei, returned as strings in `result`), plus `suggestBaseFee`

Example `result` payload:

```json
{
  "LastBlock": "19640000",
  "SafeGasPrice": "12",
  "ProposeGasPrice": "13",
  "FastGasPrice": "15",
  "suggestBaseFee": "11.85"
}
```

Map the three price points to tiers: Safe → slow, Propose → standard, Fast → fast; derive
the instant tier locally from fee-history percentiles.

### RPC `eth_feeHistory` (No-Key Fallback)

- **Endpoint**: any Ethereum JSON-RPC provider (Alchemy, Infura, or a public RPC URL)
- **Auth**: none beyond the RPC URL itself
- **Data**: recent base fees + priority-fee reward percentiles; compute slow/standard/fast/instant tiers locally from the percentile spread

> **Migration note (2026-06-19)**: the third-party mempool gas-prediction API this
> plugin previously documented shut down on 2026-06-19 and was removed as a data
> source. Its confidence-based next-block predictions have no direct equivalent above —
> tiers are approximated from Etherscan's three price points and `eth_feeHistory`
> reward percentiles instead.

## Component Design

### gas_fetcher.py

```python
class GasFetcher:
    def __init__(self, chain: str = "ethereum", rpc_url: str = None, api_key: str = None, verbose: bool = False)
    def get_current_gas(self) -> GasData
    def get_base_fee_history(self, blocks: int = 100) -> List[BaseFeeHistory]
    def get_gas_for_chain(self, chain: str) -> GasData  # For cross-chain comparison
```

### pattern_analyzer.py

```python
class PatternAnalyzer:
    def __init__(self, history_file: str = None, verbose: bool = False)
    def record_gas_data(self, gas_gwei: float) -> None
    def analyze_hourly_pattern(self) -> List[HourlyPattern]
    def analyze_daily_pattern(self) -> List[DailyPattern]
    def find_optimal_window(self, current_gas_gwei: float = None) -> TimeWindow
    def predict_gas(self, target_time: datetime) -> GasPrediction
```

### cost_estimator.py

```python
class CostEstimator:
    def __init__(self, native_symbol: str = "ETH", verbose: bool = False)
    def estimate_cost(self, operation: str, gas_price_gwei: float, tier: str = "standard", custom_gas_limit: int = None) -> CostEstimate
    def estimate_all_tiers(self, operation: str, gas_slow: float, gas_standard: float, gas_fast: float, gas_instant: float, custom_gas_limit: int = None) -> MultiTierEstimate
    def estimate_transfer(self, gas_price_gwei: float) -> CostEstimate
    def estimate_swap(self, gas_price_gwei: float, dex: str = "uniswap_v2") -> CostEstimate
    def estimate_nft_mint(self, gas_price_gwei: float) -> CostEstimate
    def estimate_custom(self, gas_price_gwei: float, gas_limit: int) -> CostEstimate
```

## Gas Price Tiers

| Tier | Percentile | Confirmation Target |
|------|------------|---------------------|
| Slow | 10th | 10+ blocks (~2+ min) |
| Standard | 50th | 3-5 blocks (~1 min) |
| Fast | 75th | 1-2 blocks (~30 sec) |
| Instant | 90th | Next block (~12 sec) |

## Historical Pattern Sources

1. **Hourly patterns**: Gas is typically lower during off-peak hours
2. **Daily patterns**: Weekends often have lower gas
3. **Event patterns**: NFT mints, token launches spike gas
4. **Network upgrades**: EIP implementations affect base fee

## Error Handling Strategy

| Error | Handling |
|-------|----------|
| RPC unavailable | Fallback to Etherscan oracle |
| Rate limited | Use cached data with staleness warning |
| Price fetch failed | Use last known good value |
| Invalid chain | Return error with supported chains list |

## Multi-Chain Support

| Chain | RPC Method | Oracle |
|-------|------------|--------|
| Ethereum | eth_feeHistory | Etherscan |
| Polygon | eth_feeHistory | Polygonscan |
| Arbitrum | eth_gasPrice | Arbiscan |
| Optimism | eth_gasPrice | Optimistic Etherscan |
| Base | eth_gasPrice | Basescan |

## Performance Considerations

- Cache gas data for 10-15 seconds
- Batch RPC calls where possible
- Store historical data locally for pattern analysis
- Limit history fetch to needed window

## Security

- No private keys required
- RPC URLs may contain API keys (handle securely)
- Read-only operations only
