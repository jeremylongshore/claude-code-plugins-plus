# Usage Examples

## Recent Whale Transactions

### View All Recent Whales

```bash
python whale_monitor.py recent
```

### Filter by Blockchain

```bash
python whale_monitor.py recent --chain ethereum
python whale_monitor.py recent --chain bitcoin
python whale_monitor.py recent --chain solana
```

### Filter by Minimum Value

```bash
python whale_monitor.py recent --min-value 1000000    # $1M+
python whale_monitor.py recent --min-value 10000000   # $10M+
python whale_monitor.py recent --min-value 100000000  # $100M+
```

### Combine Filters

```bash
python whale_monitor.py recent --chain ethereum --min-value 5000000 --limit 50
```

### Show Full Addresses

```bash
python whale_monitor.py recent --addresses
```

## Exchange Flow Analysis

### Overall Exchange Flows

```bash
python whale_monitor.py flows
```

### Chain-Specific Flows

```bash
python whale_monitor.py flows --chain ethereum
python whale_monitor.py flows --chain bitcoin
```

### Large Flows Only

```bash
python whale_monitor.py flows --min-value 10000000
```

## Watchlist Management

### View Watchlist

```bash
python whale_monitor.py watchlist
```

### Add Wallet to Watchlist

```bash
python whale_monitor.py watch 0x1234... --name "Whale Wallet 1"
python whale_monitor.py watch 0xabcd... --name "Smart Money" --chain ethereum
python whale_monitor.py watch bc1q... --name "BTC Whale" --chain bitcoin --notes "Large holder since 2017"
```

### Remove from Watchlist

```bash
python whale_monitor.py unwatch 0x1234...
```

## Track Specific Wallets

### Track Known Wallet

```bash
python whale_monitor.py track 0x28c6c06298d514db089934071355e5743bf21d60
```

### Track with Chain Specified

```bash
python whale_monitor.py track bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h --chain bitcoin
```

## Wallet Labels

### Search Labels

```bash
python whale_monitor.py labels --query binance
python whale_monitor.py labels --query kraken
python whale_monitor.py labels --query aave
```

### List by Type

```bash
python whale_monitor.py labels --type exchange
python whale_monitor.py labels --type protocol
python whale_monitor.py labels --type fund
python whale_monitor.py labels --type bridge
```

## Output Formats

### JSON Output

```bash
python whale_monitor.py recent --format json
python whale_monitor.py flows --format json > flows.json
```

### Alert Style Output

```bash
python whale_monitor.py recent --format alert
```

## API Status

### Check API Status

```bash
python whale_monitor.py status
```

## Verbose Mode

### Enable Debug Output

```bash
python whale_monitor.py recent -v
python whale_monitor.py flows -v --chain ethereum
```

## Common Workflows

### Daily Whale Monitoring

```bash
# Morning check
python whale_monitor.py recent --min-value 5000000 --limit 30
python whale_monitor.py flows

# Watch for large movements
python whale_monitor.py recent --min-value 50000000
```

### Exchange Deposit/Withdrawal Analysis

```bash
# Check if whales are depositing (selling pressure)
python whale_monitor.py flows --chain ethereum

# Large deposits = potential selling
# Large withdrawals = potential accumulation
```

### Track Specific Protocol Treasury

```bash
# Add protocol wallet to watchlist
python whale_monitor.py watch 0xbe0eb53f46cd790cd13851d5eff43d12404d33e8 --name "Aave Treasury"

# Track its activity
python whale_monitor.py track 0xbe0eb53f46cd790cd13851d5eff43d12404d33e8
```

## Programmatic Usage

```python
from whale_api import WhaleAlertClient
from wallet_labels import WalletLabeler
from price_service import PriceService

# Initialize clients
client = WhaleAlertClient()
labeler = WalletLabeler()
prices = PriceService()

# Get recent whale transactions
txs = client.get_transactions(min_value=1000000, limit=10)

for tx in txs:
    # Enrich with labels
    from_label = labeler.label_wallet(tx.from_address)
    to_label = labeler.label_wallet(tx.to_address)

    print(f"{tx.amount} {tx.symbol} ({tx.amount_usd:,.0f} USD)")
    print(f"  From: {from_label.name}")
    print(f"  To: {to_label.name}")
    print()
```

## Integration Examples

### Pipe to jq for JSON Processing

```bash
python whale_monitor.py recent --format json | jq '.[] | select(.amount_usd > 10000000)'
```

### Export to CSV

```bash
python whale_monitor.py recent --format json | \
  jq -r '.[] | [.timestamp, .blockchain, .symbol, .amount, .amount_usd, .from_owner, .to_owner] | @csv'
```

### Filter and Count

```bash
python whale_monitor.py recent --format json --limit 100 | \
  jq '[.[] | select(.to_owner_type == "exchange")] | length'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
