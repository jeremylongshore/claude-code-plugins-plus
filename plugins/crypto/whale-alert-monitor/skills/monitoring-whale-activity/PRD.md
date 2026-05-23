# PRD: Whale Alert Monitor

## Summary

**One-liner**: Track large cryptocurrency transactions and whale wallet movements in real-time
**Domain**: Cryptocurrency / On-Chain Analytics / Market Intelligence
**Users**: Traders, Analysts, Researchers, Fund Managers

## Problem Statement

Large cryptocurrency holders ("whales") can significantly impact market prices when they move funds. Traders need visibility into these movements to:

- Anticipate potential market volatility
- Identify accumulation or distribution patterns
- Track known whale wallets for trading signals
- Monitor exchange inflows/outflows for price predictions

Currently, tracking whale activity requires manually monitoring multiple sources, subscribing to expensive services, or running complex blockchain queries.

## User Stories

1. **As a trader**, I want to see large transfers happening in real-time, so I can anticipate potential price movements.
   - Acceptance: Shows transfers above threshold with USD value, source/destination labels

2. **As an analyst**, I want to track specific whale wallets over time, so I can identify accumulation/distribution patterns.
   - Acceptance: Can add wallets to watchlist, shows historical activity summary

3. **As a researcher**, I want to analyze exchange inflows/outflows, so I can predict buying/selling pressure.
   - Acceptance: Shows net flow by exchange with historical trends

4. **As a fund manager**, I want alerts when monitored wallets move funds, so I can react quickly.
   - Acceptance: Configurable thresholds, clear alert formatting

## Functional Requirements

- **REQ-1**: Monitor real-time large transfers across major chains (ETH, BTC, SOL, etc.)
- **REQ-2**: Label known wallets (exchanges, funds, bridges, known whales)
- **REQ-3**: Calculate USD value of transfers at time of transaction
- **REQ-4**: Track wallet watchlists with historical activity
- **REQ-5**: Analyze exchange inflow/outflow patterns
- **REQ-6**: Support multiple output formats (table, JSON, alerts)
- **REQ-7**: Filter by chain, token, minimum value, wallet type

## API Integrations

| API | Purpose | Auth |
|-----|---------|------|
| Whale Alert API | Real-time whale transactions | API key (free tier available) |
| Etherscan | Ethereum transaction details | API key (free tier) |
| Blockchain.com | Bitcoin transaction data | No auth for basic |
| CoinGecko | USD price conversion | No auth for basic |

## Success Metrics

- Real-time alerts with < 60 second delay from on-chain confirmation
- Accurate wallet labeling for top 100 exchanges and known funds
- USD value accuracy within 1% of market price at transaction time
- Support for at least 5 major blockchains

## Non-Goals

- Automated trading based on whale alerts
- Wallet balance tracking (use blockchain-explorer for that)
- Historical whale pattern ML/AI predictions
- Social media whale alert aggregation
