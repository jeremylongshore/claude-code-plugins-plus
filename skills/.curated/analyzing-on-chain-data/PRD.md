# PRD: On-Chain Analytics

## Summary

**One-liner**: Analyze blockchain metrics including TVL, protocol revenues, user activity, and network health across DeFi protocols.
**Domain**: Cryptocurrency / On-Chain Intelligence
**Users**: Analysts, Researchers, Traders, Protocol Teams

## Problem Statement

On-chain data is scattered across multiple sources (DeFiLlama, Dune, Flipside) with different formats and query methods. Users need unified analytics to understand protocol health, compare DeFi metrics, and identify trends without writing complex SQL queries.

## User Stories

1. **As a DeFi analyst**, I want to compare TVL across protocols, so that I can identify market leaders and growth trends.

2. **As a researcher**, I want to analyze protocol revenue and fees, so that I can evaluate sustainability and tokenomics.

3. **As a trader**, I want to track user activity and growth metrics, so that I can identify emerging protocols early.

4. **As a protocol team**, I want to monitor our on-chain metrics vs competitors, so that we can track market position.

## Functional Requirements

- REQ-1: Fetch and compare TVL across protocols and chains
- REQ-2: Analyze protocol revenues, fees, and P/E ratios
- REQ-3: Track active users (DAU/MAU/WAU) and growth rates
- REQ-4: Monitor transaction volumes and gas consumption
- REQ-5: Calculate protocol dominance and market share
- REQ-6: Generate time-series charts and comparisons
- REQ-7: Support filtering by chain, category, and time range

## API Integrations

| API | Purpose | Rate Limit |
|-----|---------|------------|
| DeFiLlama | TVL, revenues, fees, chains | No limit |
| Token Terminal | Protocol metrics, P/E ratios | 100/day (free) |
| Dune Analytics | Custom queries, user counts | 10 queries (free) |
| CoinGecko | Token prices, market caps | 10-30/min |

## Success Metrics

- TVL queries return data for top 100 protocols
- Revenue data available for 50+ protocols
- Historical data spans at least 1 year
- Output formats: table, JSON, CSV, charts

## Non-Goals

- Real-time transaction monitoring (use whale-alert-monitor)
- Individual wallet tracking (use blockchain-explorer)
- Trading recommendations or signals
- Smart contract auditing
