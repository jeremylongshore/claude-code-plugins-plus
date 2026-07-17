---
name: alchemy-reference-architecture
description: 'Implement reference architecture for Alchemy-powered Web3 applications.

  Use when designing dApp infrastructure, planning multi-chain deployments,

  or structuring a production blockchain application.

  Trigger: "alchemy architecture", "dApp architecture", "alchemy project structure",

  "web3 system design", "alchemy multi-chain design".

  '
allowed-tools: Read, Write, Edit
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- blockchain
- web3
- alchemy
- architecture
compatibility: Designed for Claude Code
---
# Alchemy Reference Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React/Next.js)              │
│  - Wallet connection (MetaMask, WalletConnect)           │
│  - Portfolio dashboard                                    │
│  - NFT gallery                                           │
│  - Transaction history                                    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS (no API key exposed)
┌────────────────────────▼────────────────────────────────┐
│                     API Layer (Next.js/Express)           │
│  - /api/balance/:address                                 │
│  - /api/nfts/:owner                                      │
│  - /api/tokens/:address                                  │
│  - /api/transactions/:address                            │
│  - /webhooks/alchemy          (webhook receiver)         │
└───────┬──────────┬──────────┬───────────────────────────┘
        │          │          │
   ┌────▼───┐ ┌───▼────┐ ┌──▼──────┐
   │Alchemy │ │Alchemy │ │Alchemy  │
   │Core API│ │NFT API │ │Notify   │
   │(RPC)   │ │        │ │(Webhooks│
   └────────┘ └────────┘ └─────────┘
   ETH/Polygon/ARB/OP/Base
```

## Project Structure

```
web3-dapp/
├── src/
│   ├── alchemy/
│   │   ├── client-factory.ts    # Multi-chain Alchemy client factory
│   │   ├── cache.ts             # Response caching with TTL
│   │   ├── throttler.ts         # CU-aware rate limiter
│   │   └── errors.ts            # Error classification
│   ├── portfolio/
│   │   ├── fetcher.ts           # Wallet portfolio aggregator
│   │   ├── transactions.ts      # Transaction history analyzer
│   │   └── multi-chain.ts       # Cross-chain balance aggregator
│   ├── nft/
│   │   ├── collection.ts        # NFT collection explorer
│   │   ├── batch-metadata.ts    # Batch metadata fetcher
│   │   └── verify-ownership.ts  # NFT ownership verification
│   ├── contracts/
│   │   ├── read-contract.ts     # Smart contract read operations
│   │   └── abis/                # Contract ABI files
│   ├── webhooks/
│   │   ├── handler.ts           # Webhook endpoint
│   │   ├── verify.ts            # HMAC signature verification
│   │   └── event-router.ts      # Event type routing
│   ├── security/
│   │   ├── validators.ts        # Input validation (addresses, blocks)
│   │   └── proxy.ts             # API key proxy for frontend
│   └── api/                     # API route handlers
├── tests/
│   ├── unit/                    # Unit tests (mocked Alchemy)
│   ├── fork/                    # Mainnet fork tests (Hardhat)
│   └── integration/             # Sepolia integration tests
├── contracts/                   # Solidity contracts (if applicable)
├── hardhat.config.ts            # Hardhat + Alchemy fork config
└── package.json
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SDK | `alchemy-sdk` | Official, typed, Enhanced + NFT APIs included |
| Multi-chain | Client factory pattern | Lazy initialization, shared API key |
| Caching | In-memory with TTL tiers | Block data = 12s, metadata = 24h |
| Rate limiting | Bottleneck with CU weights | Matches Alchemy CU budget model |
| Frontend access | API proxy | Never expose API key to browser |
| Real-time | WebSocket subscriptions | Lower cost than polling |
| Testing | Hardhat mainnet fork | Reproducible tests with real data |

## Output

- Complete project structure for Alchemy-powered dApp
- Multi-chain architecture with client factory
- API proxy pattern keeping API key server-side
- Webhook integration for real-time event processing

## Resources

- [Alchemy Docs](https://www.alchemy.com/docs)
- [Alchemy SDK GitHub](https://github.com/alchemyplatform/alchemy-sdk-js)
- [Alchemy Dashboard](https://dashboard.alchemy.com)

## Next Steps

Start with `alchemy-install-auth`, then follow skills through production deployment.
