---
name: monitoring-whale-activity
description: |
  Track large cryptocurrency transactions and whale wallet movements in real-time.
  Use when tracking large holder movements, exchange flows, or wallet activity.
  Trigger with phrases like "track whales", "monitor large transfers", "check whale activity", "exchange inflows", or "watch wallet".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*whale*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Monitoring Whale Activity

## Overview

Track large cryptocurrency transactions and whale wallet movements across multiple blockchains. Monitor exchange inflows/outflows, manage watchlists, and identify known wallets (exchanges, funds, bridges).

## Prerequisites

Before using this skill, ensure you have:
- Python 3.8+ with requests library
- Whale Alert API key (optional, for live data - free tier available)
- Internet access for API calls

## Instructions

### Step 1: Navigate to Scripts Directory

```bash
cd {baseDir}/scripts
```

### Step 2: Choose Your Command

**Recent Whale Transactions:**
```bash
python whale_monitor.py recent                    # All chains
python whale_monitor.py recent --chain ethereum   # Specific chain
python whale_monitor.py recent --min-value 10000000  # $10M+ only
```

**Exchange Flow Analysis:**
```bash
python whale_monitor.py flows                     # Overall exchange flows
python whale_monitor.py flows --chain ethereum    # Chain-specific
```

**Watchlist Management:**
```bash
python whale_monitor.py watchlist                 # View watchlist
python whale_monitor.py watch 0x123... --name "My Whale"  # Add to watchlist
python whale_monitor.py unwatch 0x123...          # Remove from watchlist
```

**Track Specific Wallet:**
```bash
python whale_monitor.py track 0x123...            # Track wallet activity
```

**Search Known Labels:**
```bash
python whale_monitor.py labels --query binance    # Search by name
python whale_monitor.py labels --type exchange    # List by type
```

### Step 3: Interpret Results

**Transaction Types:**
- 🔴 DEPOSIT → Exchange (potential selling pressure)
- 🟢 WITHDRAWAL → From exchange (accumulation signal)
- 🐋 TRANSFER → Wallet to wallet (whale movement)

**Flow Analysis:**
- Net positive flow to exchanges = selling pressure
- Net negative flow from exchanges = buying pressure

## Output

- Real-time whale transactions with USD values
- Labeled wallets (exchanges, funds, bridges, protocols)
- Exchange inflow/outflow summaries
- Custom watchlist tracking
- JSON, table, or alert format output

## Error Handling

See `{baseDir}/references/errors.md` for:
- API rate limit handling
- Network timeout recovery
- Invalid address formats
- Price service fallbacks

## Examples

**View $10M+ whale transactions on Ethereum:**
```bash
python whale_monitor.py recent --chain ethereum --min-value 10000000
```

**Analyze if whales are selling (depositing to exchanges):**
```bash
python whale_monitor.py flows --chain ethereum
```

**Track a known whale wallet:**
```bash
python whale_monitor.py watch 0x28c6c... --name "Binance Cold"
python whale_monitor.py track 0x28c6c...
```

**Export to JSON for further analysis:**
```bash
python whale_monitor.py recent --format json > whales.json
```

See `{baseDir}/references/examples.md` for more usage patterns.

## Resources

- [Whale Alert](https://whale-alert.io) - Real-time whale transaction API
- [Etherscan](https://etherscan.io) - Ethereum blockchain explorer
- [CoinGecko](https://coingecko.com) - Price data API
- Known wallet database with 100+ labeled exchanges and protocols
