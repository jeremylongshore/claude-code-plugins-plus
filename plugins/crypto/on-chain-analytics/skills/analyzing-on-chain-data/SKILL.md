---
name: analyzing-on-chain-data
description: |
  Process perform on-chain analysis including whale tracking, token flows, and network activity.
  Use when performing crypto analysis.
  Trigger with phrases like "analyze crypto", "check blockchain", or "monitor market".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:onchain-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Analyzing On Chain Data

## Overview

This skill provides automated assistance for the described functionality.

## Prerequisites

Before using this skill, ensure you have:
- Access to crypto market data APIs (CoinGecko, CoinMarketCap, or similar)
- Blockchain RPC endpoints or node access (Alchemy, Chainstack, Infura, or self-hosted)
- API keys for exchanges if trading or querying account data
- Web3 libraries installed (ethers.js, web3.py, or equivalent)
- Understanding of blockchain concepts and crypto market dynamics

## Instructions

1. Use Read tool to load API credentials from {baseDir}/config/crypto-apis.env
2. Configure blockchain RPC endpoints for target networks
3. Set up exchange API connections if required
4. Verify rate limits and subscription tiers
5. Test connectivity and authentication
1. Use Bash(crypto:onchain-*) to execute crypto data queries
2. Fetch real-time prices, volumes, and market cap data
3. Query blockchain for on-chain metrics and transactions
4. Retrieve exchange order book and trade history
5. Aggregate data from multiple sources for accuracy


See `{baseDir}/references/implementation.md` for detailed implementation guide.

## Output

- Current prices across exchanges with spread analysis
- 24h volume, market cap, and circulating supply
- Price changes across multiple timeframes (1h, 24h, 7d, 30d)
- Trading volume distribution by exchange
- Liquidity metrics and slippage estimates
- Transaction count and network activity

## Error Handling

See `{baseDir}/references/errors.md` for comprehensive error handling.

## Examples

See `{baseDir}/references/examples.md` for detailed examples.

## Resources

- CoinGecko API for market data across thousands of assets
- Etherscan API for Ethereum blockchain data
- Dune Analytics for on-chain SQL queries
- The Graph for decentralized blockchain indexing
- ethers.js for Ethereum smart contract interaction
