# ARD: Whale Alert Monitor

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Script Automation Pattern** - Python CLI that fetches whale transaction data from APIs, labels wallets, and presents formatted output.

## Workflow

```
User Request → Parse Filters → Fetch Whale Data → Label Wallets → Format Output
     ↓              ↓              ↓                  ↓             ↓
  "show whales"  chain/min_value  Whale Alert API   Exchange DB   Table/JSON
```

## Data Flow

```
Input: User parameters (chain, min_value, wallet_type, watchlist)
          ↓
API Layer: Whale Alert API → Recent large transactions
          ↓
Enrichment: Label wallets (exchange, fund, bridge, unknown)
          ↓
Pricing: CoinGecko → USD value at transaction time
          ↓
Output: Formatted table, JSON, or alert format
```

## Directory Structure

```
skills/monitoring-whale-activity/
├── PRD.md                    # This requirements doc
├── ARD.md                    # This architecture doc
├── SKILL.md                  # Agent instructions
├── scripts/
│   ├── whale_monitor.py      # Main CLI entry point
│   ├── whale_api.py          # Whale Alert API client
│   ├── wallet_labels.py      # Known wallet database
│   ├── price_service.py      # USD price lookup
│   └── formatters.py         # Output formatting
├── references/
│   ├── errors.md             # Error handling guide
│   └── examples.md           # Usage examples
└── config/
    └── settings.yaml         # Default configuration
```

## API Integration

### Whale Alert API

- **Endpoint**: `https://api.whale-alert.io/v1/transactions`
- **Auth**: API key in header
- **Rate Limits**: 10 req/min (free), 100 req/min (paid)
- **Data**: Real-time large transactions across chains

### Etherscan (Fallback)

- **Endpoint**: `https://api.etherscan.io/api`
- **Auth**: API key in query param
- **Rate Limits**: 5 req/sec (free)
- **Data**: Ethereum transaction details

## Component Design

### whale_api.py

```python
class WhaleAlertClient:
    def get_transactions(chain, min_value, limit) -> List[Transaction]
    def get_transaction_details(tx_hash) -> TransactionDetail
```

### wallet_labels.py

```python
class WalletLabeler:
    def label_wallet(address, chain) -> WalletLabel
    def add_to_watchlist(address, name) -> None
    def get_watchlist() -> List[WatchlistEntry]
```

### price_service.py

```python
class PriceService:
    def get_price(symbol, timestamp=None) -> float
    def convert_to_usd(amount, symbol) -> float
```

## Error Handling Strategy

| Error | Handling |
|-------|----------|
| API rate limit | Exponential backoff, show cached data |
| Invalid API key | Clear error message with setup instructions |
| Network timeout | Retry 3x with increasing delay |
| Unknown wallet | Label as "Unknown" with address prefix |
| Price unavailable | Show token amount without USD conversion |

## Wallet Label Database

Built-in labels for:

- **Exchanges**: Binance, Coinbase, Kraken, OKX, Bybit, etc.
- **Bridges**: Wormhole, LayerZero, Stargate, Multichain
- **Funds**: Known VC/fund wallets (a16z, Paradigm, etc.)
- **Protocols**: Major DeFi protocol treasuries

## Performance Considerations

- Cache wallet labels (rarely change)
- Cache prices for 60 seconds
- Stream mode for continuous monitoring
- Batch API requests where possible

## Security

- API keys stored in environment variables or config file
- No private keys or wallet access required
- Read-only blockchain queries
