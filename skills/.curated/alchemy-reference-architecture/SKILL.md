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

## Overview

This reference architecture separates wallet-facing UI from server-side
provider access so API keys, rate limits, validation, caching, and webhook
verification are consistently controlled across supported chains.

## Prerequisites

- A written data-flow and threat model covering wallet addresses, signed
  messages, provider credentials, public API routes, and webhook events.
- A server-side deployment target with managed secrets, input validation,
  rate limiting, and observability before any frontend endpoint is exposed.
- Public-chain or testnet fixtures and a rollback mechanism for each feature
  that affects external users or contract interactions.

## Instructions

1. Begin with a single chain and server-side client factory, keeping the
   provider key out of browser bundles and public response payloads.
2. Add validated, rate-limited API routes for each use case and define the
   cache freshness rule before implementing UI data fetching.
3. Treat a wallet address as an identifier, not authentication; use a
   signed challenge when ownership must be proved.
4. Verify webhook signatures and idempotency before routing any external event,
   then test the complete path against public or testnet fixtures.

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

## Examples

Implement the balance route for one public test address in a staging service.
The frontend calls the route without an Alchemy key, while the server validates
the address, uses the managed secret, applies the balance freshness TTL, and
emits only aggregate latency and outcome telemetry. Confirm a malformed address
is rejected before provider use and a simulated provider outage yields a clear
unavailable response. If the key appears in a browser artifact, the route lacks
rate limiting, or the failure state is ambiguous, keep the feature disabled and
fix that boundary before adding multi-chain or wallet-gated behavior.

## Error Handling

| Failure | Architecture response |
|---------|-----------------------|
| Browser bundle contains provider credential | Revoke the credential, remove it from the artifact, and enforce server-side access. |
| Public route receives malformed or abusive input | Reject early, apply rate limits, and do not forward the request to the provider. |
| Webhook is unsigned or duplicate | Reject it or return a safe duplicate response before business processing. |
| Provider or chain is unavailable | Return explicit partial/unavailable state and activate the product fallback. |

## Resources

- [Alchemy Docs](https://www.alchemy.com/docs)
- [Alchemy SDK GitHub](https://github.com/alchemyplatform/alchemy-sdk-js)
- [Alchemy Dashboard](https://dashboard.alchemy.com)

## Next Steps

Start with `alchemy-install-auth`, then follow skills through production deployment.
