# PRD: Gas Fee Optimizer

## Summary

**One-liner**: Predict optimal gas prices and timing to minimize blockchain transaction costs
**Domain**: Cryptocurrency / Blockchain / Transaction Optimization
**Users**: Traders, DeFi Users, NFT Collectors, Protocol Developers

## Problem Statement

Blockchain transaction fees can vary dramatically based on:

- Network congestion (pending transaction volume)
- Time of day/week (weekends often cheaper)
- Block space competition (NFT mints, token launches)
- Base fee dynamics (EIP-1559 mechanisms)

Users often overpay for gas or have transactions stuck due to poor fee estimation. Without proper tools, users either:

- Pay excessive fees for fast confirmation
- Set fees too low and wait hours/days
- Miss optimal timing windows for cheap transactions

## User Stories

1. **As a DeFi user**, I want to know the best time to make my swap, so I can minimize transaction costs.
   - Acceptance: Shows hourly gas trends, recommends optimal timing windows

2. **As an NFT collector**, I want gas alerts when fees drop below threshold, so I can mint at low cost.
   - Acceptance: Configurable threshold alerts, historical low comparisons
   - *Note: Alerting feature planned for v2.0. Current version supports on-demand price checks.*

3. **As a trader**, I want accurate gas estimates for different confirmation speeds, so I can choose cost vs speed.
   - Acceptance: Shows slow/standard/fast/instant with estimated times and costs

4. **As a protocol developer**, I want to understand gas trends for my contracts, so I can advise users.
   - Acceptance: Gas estimation for specific contract calls, historical analysis

## Functional Requirements

- **REQ-1**: Fetch real-time gas prices from multiple sources
- **REQ-2**: Analyze historical gas patterns (hourly, daily, weekly)
- **REQ-3**: Recommend optimal transaction timing
- **REQ-4**: Estimate gas cost for standard operations (transfer, swap, mint)
- **REQ-5**: Alert when gas drops below user-defined threshold *(planned for v2.0)*
- **REQ-6**: Support multiple chains (Ethereum, Polygon, Arbitrum, etc.)
- **REQ-7**: Calculate USD cost of transactions

## API Integrations

| API | Purpose | Auth |
|-----|---------|------|
| Ethereum RPC (`eth_feeHistory`) | Real-time gas prices, base-fee history fallback | RPC URL (Alchemy/Infura or public endpoint, no key required) |
| Etherscan Gas Oracle | Gas oracle (primary) | `ETHERSCAN_API_KEY` (free key, 5 calls/sec) |
| CoinGecko | ETH/MATIC price for USD conversion | No auth |

## Success Metrics

- Gas recommendations accurate within 10% of optimal
- Historical pattern detection with 80%+ accuracy
- Support for at least 5 major EVM chains
- Real-time updates with < 5 second lag

## Non-Goals

- Automated transaction submission
- Gas token (CHI, GST2) optimization
- Flashbots/MEV bundle submission
- Layer 2 bridging cost optimization
