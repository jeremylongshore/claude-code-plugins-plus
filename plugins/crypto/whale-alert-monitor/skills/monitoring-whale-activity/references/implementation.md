# Implementation Details

## Transaction Type Classification

The monitor classifies whale transactions by flow direction:
- **DEPOSIT** (exchange inflow): Wallet sends to known exchange address. Signals potential selling pressure.
- **WITHDRAWAL** (exchange outflow): Known exchange sends to external wallet. Signals accumulation.
- **TRANSFER**: Wallet-to-wallet movement between non-exchange addresses. May indicate OTC deals, fund rebalancing, or cold storage rotation.

## Flow Analysis Interpretation

Exchange flow analysis aggregates deposits and withdrawals over a time window:
- **Net positive flow** to exchanges = more tokens entering exchanges than leaving = selling pressure
- **Net negative flow** from exchanges = more tokens leaving exchanges than entering = buying pressure
- **Neutral flow** = balanced activity, no clear directional signal

Typical flow thresholds for significance:
| Chain | Significant Net Flow | Major Net Flow |
|-------|---------------------|----------------|
| Ethereum | > $50M/day | > $200M/day |
| Bitcoin | > $100M/day | > $500M/day |

## Known Wallet Database

The monitor maintains a database of 100+ labeled addresses including:
- **Exchanges**: Binance, Coinbase, Kraken, FTX, Gemini hot/cold wallets
- **Funds**: Grayscale, Jump Trading, Three Arrows Capital
- **Bridges**: Wormhole, Multichain, Arbitrum Bridge
- **Protocols**: Lido, Aave, Compound treasury addresses

Search labels with:
```bash
python whale_monitor.py labels --query binance    # Search by name
python whale_monitor.py labels --type exchange    # List by type (exchange, fund, bridge, protocol)
```

## Watchlist Persistence

Watchlists are stored in `${CLAUDE_SKILL_DIR}/config/watchlist.json`:
```json
{
  "wallets": [
    {
      "address": "0x28c6c...",
      "name": "Binance Cold",
      "added": "2024-01-15",
      "chain": "ethereum"
    }
  ]
}
```

## Multi-Chain Support

| Chain | Min Whale Threshold | Data Source |
|-------|-------------------|-------------|
| Ethereum | $1M | Whale Alert API + Etherscan |
| Bitcoin | $1M | Whale Alert API + Blockchain.com |
| Tron | $500K | Whale Alert API + Tronscan |
| Ripple | $500K | Whale Alert API |

## Output Formats

**Table format** (default): Human-readable with color indicators
**JSON format** (`--format json`): Machine-readable for pipeline integration
**Alert format** (`--format alert`): Compact one-line-per-transaction for monitoring
