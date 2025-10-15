# Crypto/Market Plugins Summary

This directory contains 6 professional cryptocurrency and market analysis plugins for Claude Code.

## Plugins Overview

### 1. Staking Rewards Optimizer
**Location**: `staking-rewards-optimizer/`
**Command**: `/optimize-staking` (shortcut: `/stake`)
**Purpose**: Optimize staking rewards across multiple protocols and blockchains

**Features**:
- Multi-chain staking comparison (Ethereum, Cosmos, Polkadot, Solana)
- Risk vs reward analysis
- Liquid staking options (Lido, Rocket Pool, Frax)
- Portfolio optimization recommendations
- APY/APR calculations with real data sources

---

### 2. NFT Rarity Analyzer
**Location**: `nft-rarity-analyzer/`
**Command**: `/analyze-nft` (shortcut: `/nft`)
**Purpose**: Analyze NFT rarity scores and valuations

**Features**:
- Trait breakdown and rarity scoring
- Multiple scoring methodologies (Statistical, Normalized, OpenRarity)
- Valuation estimates based on comparables
- Collection metrics and floor price analysis
- Investment recommendations

---

### 3. Gas Fee Optimizer
**Location**: `gas-fee-optimizer/`
**Command**: `/optimize-gas` (shortcut: `/gas`)
**Purpose**: Optimize Ethereum transaction gas fees

**Features**:
- Real-time gas price analysis
- Historical pattern identification
- Best time windows for transactions
- Layer 2 cost comparison (Arbitrum, Optimism, Base, zkSync)
- Sidechain alternatives (Polygon, Gnosis)
- Cost-benefit analysis for timing

---

### 4. DEX Aggregator Router
**Location**: `dex-aggregator-router/`
**Command**: `/find-best-route` (shortcut: `/route`)
**Purpose**: Find optimal DEX routes for token swaps

**Features**:
- Multi-DEX comparison (Uniswap, SushiSwap, Curve, Balancer)
- Direct, multi-hop, and split routing
- Price impact calculations
- Gas cost optimization
- Slippage recommendations
- MEV protection guidance

---

### 5. Crypto Signal Generator
**Location**: `crypto-signal-generator/`
**Command**: `/generate-signal` (shortcut: `/signal`)
**Purpose**: Generate trading signals from technical indicators

**Features**:
- Comprehensive technical indicator analysis (RSI, MACD, Bollinger Bands)
- Chart pattern recognition
- Multi-timeframe confluence (15m, 1H, 4H, Daily, Weekly)
- Entry/exit strategy with stop-loss and take-profit levels
- Risk/reward calculations
- Position sizing recommendations

---

### 6. Blockchain Explorer CLI
**Location**: `blockchain-explorer-cli/`
**Command**: `/explore`
**Purpose**: Command-line blockchain data exploration

**Features**:
- Address analysis (balance, tokens, NFTs, transaction history)
- Transaction lookup (status, gas, decoded input)
- Smart contract analysis (verification, security, functions)
- Block information
- Token analytics
- Multi-network support (Ethereum, Polygon, Arbitrum, Optimism, Base)

---

## Installation

Users can install individual plugins:

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install staking-rewards-optimizer@claude-code-plugins-plus
/plugin install nft-rarity-analyzer@claude-code-plugins-plus
/plugin install gas-fee-optimizer@claude-code-plugins-plus
/plugin install dex-aggregator-router@claude-code-plugins-plus
/plugin install crypto-signal-generator@claude-code-plugins-plus
/plugin install blockchain-explorer-cli@claude-code-plugins-plus
```

## Plugin Categories

All plugins are categorized as `crypto` in the marketplace.

## Common Use Cases

### For DeFi Users
- **Staking Optimizer**: Maximize yield across protocols
- **Gas Optimizer**: Minimize transaction costs
- **DEX Router**: Get best swap rates

### For Traders
- **Signal Generator**: Technical analysis and entry/exit points
- **Gas Optimizer**: Time trades for lower costs
- **Blockchain Explorer**: Verify transactions

### For NFT Collectors
- **Rarity Analyzer**: Evaluate NFT rarity and value
- **Gas Optimizer**: Mint during low gas periods
- **Blockchain Explorer**: Research collections

### For Developers
- **Blockchain Explorer**: Analyze smart contracts
- **Gas Optimizer**: Optimize contract deployments
- **DEX Router**: Understand routing mechanics

## Data Sources

Plugins reference data from:
- **DeFi**: DefiLlama, StakingRewards.com
- **NFTs**: OpenSea, Rarity.tools, LooksRare
- **Gas**: Etherscan, Blocknative, ETH Gas Station
- **DEX**: 1inch, Paraswap, on-chain pools
- **Blockchain**: Etherscan, network-specific explorers

## Important Disclaimers

All plugins provide:
-  Educational analysis and information
-  Data-driven recommendations
-  Technical guidance

All plugins do NOT provide:
-  Financial advice
-  Investment recommendations
-  Guaranteed outcomes

Users should:
- Always do their own research (DYOR)
- Understand risks involved
- Only invest what they can afford to lose
- Consider consulting licensed financial advisors

## Plugin Structure

Each plugin follows the standard structure:
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── commands/
│   └── command-name.md      # Main command implementation
└── README.md                # User documentation
```

## Development Notes

- All JSON files validated with `jq`
- Commands include comprehensive prompt engineering
- Output formats designed for readability
- Risk warnings included in all financial plugins
- Multi-network support where applicable

## Version History

- **v1.0.0** (2025-10-11): Initial release of all 6 plugins

---

**Last Updated**: October 11, 2025
**Status**: Production Ready
**Maintainer**: Claude Code Plugins Community
