# PRD: Blockchain Explorer CLI

## Summary
**One-liner**: Query and analyze blockchain data including blocks, transactions, addresses, and smart contracts across multiple chains.
**Domain**: Cryptocurrency / Blockchain Analytics
**Users**: Developers, Analysts, Traders, Researchers

## Problem Statement
Blockchain data is scattered across multiple explorers and APIs with inconsistent interfaces. Users need a unified CLI to query blocks, transactions, addresses, and contracts without switching between different blockchain explorers or writing custom scripts.

## User Stories

1. **As a developer**, I want to query transaction details by hash, so that I can debug failed transactions or verify contract interactions.

2. **As a trader**, I want to check wallet balances and transaction history, so that I can track whale movements or verify my own transfers.

3. **As an analyst**, I want to fetch block data and network statistics, so that I can analyze network health and congestion.

4. **As a researcher**, I want to query smart contract state and events, so that I can analyze protocol behavior and token metrics.

## Functional Requirements

- REQ-1: Query transaction details by hash (status, gas, value, input data)
- REQ-2: Fetch address balances (native + ERC20/ERC721 tokens)
- REQ-3: Get block information (number, timestamp, transactions, gas)
- REQ-4: Query smart contract read functions
- REQ-5: Fetch transaction history for addresses
- REQ-6: Support multiple chains (Ethereum, Polygon, BSC, Arbitrum, etc.)
- REQ-7: Decode transaction input data using ABI
- REQ-8: Display token transfers within transactions

## API Integrations

| API | Purpose | Rate Limit |
|-----|---------|------------|
| Etherscan | Ethereum data, ABI, source code | 5/sec (free) |
| Alchemy, Chainstack, Infura | RPC providers for real-time data | Provider-plan dependent |
| CoinGecko | Token prices for USD values | 10-30/min |
| Polygonscan | Polygon chain data | 5/sec (free) |
| BSCScan | BSC chain data | 5/sec (free) |

## Success Metrics

- Transaction queries return complete data within 3 seconds
- Multi-chain support for top 5 EVM chains
- Error messages include actionable remediation steps
- Output formats: table, JSON, CSV

## Non-Goals

- Real-time transaction monitoring (use whale-alert-monitor)
- Gas price optimization (use gas-fee-optimizer)
- Non-EVM chains (Solana, Bitcoin) in v1.0
- Private transaction decryption
