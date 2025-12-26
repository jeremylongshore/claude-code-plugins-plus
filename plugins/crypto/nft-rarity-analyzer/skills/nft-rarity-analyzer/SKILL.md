---
name: analyzing-nft-rarity
description: |
  Calculate NFT rarity scores and floor prices across collections and marketplaces.
  Use when analyzing NFT collections and rarity.
  Trigger with phrases like "check NFT rarity", "analyze collection", or "calculate floor price".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:nft-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure you have:
- Access to crypto market data APIs (CoinGecko, CoinMarketCap, or similar)
- Blockchain RPC endpoints or node access (Infura, Alchemy, or self-hosted)
- API keys for exchanges if trading or querying account data
- Web3 libraries installed (ethers.js, web3.py, or equivalent)
- Understanding of blockchain concepts and crypto market dynamics

## Instructions

### Step 1: Configure Data Sources
Set up connections to crypto data providers:
1. Use Read tool to load API credentials from {baseDir}/config/crypto-apis.env
2. Configure blockchain RPC endpoints for target networks
3. Set up exchange API connections if required
4. Verify rate limits and subscription tiers
5. Test connectivity and authentication

### Step 2: Query Crypto Data
Retrieve relevant blockchain and market data:
1. Use Bash(crypto:nft-*) to execute crypto data queries
2. Fetch real-time prices, volumes, and market cap data
3. Query blockchain for on-chain metrics and transactions
4. Retrieve exchange order book and trade history
5. Aggregate data from multiple sources for accuracy

### Step 3: Analyze and Process
Process crypto data to generate insights:
- Calculate key metrics (returns, volatility, correlation)
- Identify patterns and anomalies in data
- Apply technical indicators or on-chain signals
- Compare across timeframes and assets
- Generate actionable insights and alerts

### Step 4: Generate Reports
Document findings in {baseDir}/crypto-reports/:
- Market summary with key price movements
- Detailed analysis with charts and metrics
- Trading signals or opportunity recommendations
- Risk assessment and position sizing guidance
- Historical context and trend analysis

## Output

The skill generates comprehensive crypto analysis:

### Market Data
Real-time and historical metrics:
- Current prices across exchanges with spread analysis
- 24h volume, market cap, and circulating supply
- Price changes across multiple timeframes (1h, 24h, 7d, 30d)
- Trading volume distribution by exchange
- Liquidity metrics and slippage estimates

### On-Chain Metrics
Blockchain-specific analysis:
- Transaction count and network activity
- Active addresses and user growth metrics
- Token holder distribution and concentration
- Smart contract interactions and DeFi TVL
- Gas usage and network congestion indicators

### Technical Analysis
Trading indicators and signals:
- Moving averages (SMA, EMA) and trend identification
- RSI, MACD, Bollinger Bands technical indicators
- Support and resistance levels
- Chart patterns and breakout signals
- Volume profile and accumulation zones

### Risk Metrics
Portfolio and position risk assessment:
- Value at Risk (VaR) calculations
- Portfolio correlation and diversification metrics
- Volatility analysis and beta to market
- Drawdown statistics and recovery times
- Liquidation risk for leveraged positions

## Error Handling

Common issues and solutions:

**API Rate Limit Exceeded**
- Error: Too many requests to crypto data API
- Solution: Implement request throttling; use caching for frequently accessed data; upgrade API tier if needed

**Blockchain RPC Errors**
- Error: Cannot connect to blockchain node or timeout
- Solution: Switch to backup RPC endpoint; verify network connectivity; check if node is synced

**Invalid Address or Transaction**
- Error: Blockchain address format invalid or transaction not found
- Solution: Validate address checksums; verify network (mainnet vs testnet); allow time for transaction confirmation

**Exchange API Authentication Failed**
- Error: Invalid API key or signature mismatch
- Solution: Regenerate API keys; verify permissions (read/trade); check system clock synchronization for signatures

## Resources

### Crypto Data Providers
- CoinGecko API for market data across thousands of assets
- Etherscan API for Ethereum blockchain data
- Dune Analytics for on-chain SQL queries
- The Graph for decentralized blockchain indexing

### Web3 Libraries
- ethers.js for Ethereum smart contract interaction
- web3.py for Python-based blockchain queries
- viem for TypeScript Web3 development
- Hardhat for local blockchain testing

### Trading and Analysis Tools
- TradingView for technical analysis and charting
- Glassnode for advanced on-chain metrics
- DeFi Llama for DeFi protocol analytics
- Nansen for wallet tracking and smart money flows

### Best Practices
- Never store private keys or seed phrases in code
- Always verify smart contract addresses from official sources
- Use testnet for experimentation before mainnet
- Implement proper error handling for network failures
- Monitor gas prices before submitting transactions
- Validate all user inputs to prevent injection attacks

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.