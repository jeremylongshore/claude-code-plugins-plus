# PRD: Token Launch Tracker

## Summary

**One-liner**: Track new token launches, liquidity additions, and upcoming IDO/IEO events across chains.

**Domain**: Cryptocurrency / DeFi / Token Launches

**Users**: Traders, Investors, Researchers, Degens

## Problem Statement

New token launches happen constantly across multiple chains and DEXes. Traders miss opportunities because they can't track all launches in real-time. Manual monitoring is time-consuming and unreliable. Existing tools are scattered across different platforms.

## User Stories

1. **As a trader**, I want to see new tokens that just added liquidity, so that I can evaluate early entry opportunities.

2. **As an investor**, I want to track upcoming IDO/IEO launches, so that I can plan participation in promising projects.

3. **As a researcher**, I want to analyze token launch patterns, so that I can identify trends and red flags.

4. **As a degen**, I want real-time alerts for new token deployments, so that I can assess them quickly.

## Functional Requirements

- **REQ-1**: Detect new token deployments on supported chains
- **REQ-2**: Track liquidity additions on major DEXes
- **REQ-3**: Fetch upcoming launches from IDO platforms
- **REQ-4**: Display token contract info (name, symbol, supply)
- **REQ-5**: Show initial liquidity amount and trading pair
- **REQ-6**: Analyze contract for common rug pull indicators
- **REQ-7**: Support multiple chains (Ethereum, BSC, Base, Arbitrum)
- **REQ-8**: Provide filtering by chain, DEX, and time window

## Data Sources

### On-Chain Detection

- Factory contract events (PairCreated)
- Token deployment transactions
- Liquidity mint events

### IDO/IEO Platforms

- CoinList
- Pinksale
- DxSale
- Unicrypt

### Aggregators

- DEXTools
- DexScreener
- GeckoTerminal

## Success Metrics

- Detect liquidity additions within 1 block
- List upcoming IDOs with correct dates
- Flag suspicious contracts accurately
- Support 5+ chains and 10+ DEXes

## Non-Goals

- Automated trading or sniping
- Financial advice on token quality
- Price predictions
- Private sale access
