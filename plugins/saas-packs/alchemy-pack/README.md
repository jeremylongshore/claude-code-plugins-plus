# Alchemy Skill Pack

> Claude Code skills for Alchemy Web3 blockchain development — NFTs, DeFi, multi-chain APIs (18 skills)

Alchemy is the leading Web3 development platform, providing blockchain infrastructure across Ethereum, Polygon, Arbitrum, Optimism, Base, and Solana. These skills use the real `alchemy-sdk` npm package with actual API methods: `getBalance`, `getTokenBalances`, `getNftsForOwner`, `getAssetTransfers`, Notify webhooks, and more.

## Installation

```bash
/plugin install alchemy-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `alchemy-install-auth` | Install `alchemy-sdk`, configure API key, multi-chain setup |
| `alchemy-hello-world` | Get ETH balance, fetch NFTs, read token balances, get block info |
| `alchemy-local-dev-loop` | Hardhat + Alchemy mainnet fork, Sepolia testnet, watch mode |
| `alchemy-sdk-patterns` | Multi-chain factory, response caching, NFT query builder |
| `alchemy-core-workflow-a` | Wallet portfolio tracker: tokens + NFTs + transaction history |
| `alchemy-core-workflow-b` | NFT collection explorer, smart contract reads, ownership verification |
| `alchemy-common-errors` | Diagnose 429s, RPC errors, NFT API issues, Enhanced API failures |
| `alchemy-debug-bundle` | Diagnostic bundle: connectivity, SDK version, multi-network status |
| `alchemy-rate-limits` | CU-aware Bottleneck throttler, batch optimizer, 429 retry handler |
| `alchemy-security-basics` | API key proxy, input validation, private key safety, webhook HMAC |
| `alchemy-prod-checklist` | Production readiness: API key exposure scan, connectivity checks |
| `alchemy-upgrade-migration` | Migrate from alchemy-web3 to alchemy-sdk, namespace changes |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `alchemy-ci-integration` | GitHub Actions with Hardhat fork tests and API key exposure scanning |
| `alchemy-deploy-integration` | Deploy to Vercel/Cloud Run with server-side API key security |
| `alchemy-webhooks-events` | Alchemy Notify: address activity, mined/dropped tx, NFT events |
| `alchemy-performance-tuning` | TTL caching, parallel multi-chain fetching, batch NFT metadata |
| `alchemy-cost-tuning` | CU usage monitoring, plan recommendations, batch optimization |
| `alchemy-reference-architecture` | Full dApp architecture with multi-chain client factory pattern |

## Key Concepts

- **Real SDK** — All code uses `alchemy-sdk` npm package (`import { Alchemy, Network } from 'alchemy-sdk'`)
- **Compute Units** — Alchemy bills by CU; skills include CU cost tables and optimization patterns
- **Multi-chain** — Factory pattern supporting ETH, Polygon, Arbitrum, Optimism, Base
- **Never expose API key** — All skills enforce server-side API key via proxy pattern

## License

MIT
