# QuickNode Skill Pack

> Claude Code skill pack for QuickNode — blockchain RPC, multi-chain APIs, Streams, and Web3 infrastructure (18 skills)

## What This Covers

QuickNode provides blockchain infrastructure with RPC endpoints for 77+ chains. This pack covers the **QuickNode SDK** (`@quicknode/sdk`) for EVM RPC calls, the **Streams** API for real-time blockchain data, **Functions** for serverless blockchain logic, and direct JSON-RPC calls.

**Key APIs:** EVM RPC (eth_blockNumber, eth_getBalance, eth_call), Solana RPC, NFT API, Token API, Streams (webhooks for on-chain events), IPFS. Auth via API key in endpoint URL.

## Installation

```bash
/plugin install quicknode-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `quicknode-install-auth` | Set up QuickNode endpoint, install `@quicknode/sdk` or ethers.js |
| `quicknode-hello-world` | First RPC call: get block number, check balance, read contract |
| `quicknode-local-dev-loop` | Local Hardhat node, mocked RPC responses, testing |
| `quicknode-sdk-patterns` | Core SDK module, viem integration, error handling |
| `quicknode-core-workflow-a` | EVM workflows: send transactions, read contracts, event logs |
| `quicknode-core-workflow-b` | NFT and token APIs: metadata, balances, transfers |
| `quicknode-common-errors` | Fix RPC errors, nonce issues, gas estimation failures |
| `quicknode-debug-bundle` | Collect RPC logs, transaction receipts, provider state |
| `quicknode-rate-limits` | Handle RPC rate limits, request queuing, WebSocket management |
| `quicknode-security-basics` | Endpoint security, private key management, RPC filtering |
| `quicknode-prod-checklist` | Production: endpoint redundancy, monitoring, fallback providers |
| `quicknode-upgrade-migration` | SDK version upgrades, chain migration |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `quicknode-ci-integration` | CI pipeline with Hardhat tests against QuickNode endpoints |
| `quicknode-deploy-integration` | Deploy dApp backends with QuickNode RPC configuration |
| `quicknode-webhooks-events` | QuickNode Streams: real-time on-chain event processing |
| `quicknode-performance-tuning` | Batch RPC calls, WebSocket subscriptions, caching |
| `quicknode-cost-tuning` | Optimize RPC credits, select appropriate plan tier |
| `quicknode-reference-architecture` | Web3 backend architecture with QuickNode infrastructure |

## Key Documentation

- [QuickNode Docs](https://www.quicknode.com/docs/welcome)
- [QuickNode SDK](https://www.quicknode.com/docs/quicknode-sdk/getting-started)
- [Ethereum API](https://www.quicknode.com/docs/ethereum)
- [Solana API](https://www.quicknode.com/docs/solana)

## License

MIT
