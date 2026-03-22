---
name: alchemy-performance-tuning
description: |
  Optimize Alchemy SDK performance with caching, batching, and multi-chain parallelism.
  Use when reducing latency for blockchain queries, optimizing CU consumption,
  or scaling dApps for high request volumes.
  Trigger: "alchemy performance", "alchemy slow", "alchemy optimization",
  "alchemy caching", "alchemy batch requests".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, performance]
compatible-with: claude-code
---

# Alchemy Performance Tuning

## Performance Targets

| Operation | Target Latency | CU Cost |
|-----------|---------------|---------|
| `getBlockNumber` | < 50ms | 10 |
| `getBalance` | < 100ms | 19 |
| `getTokenBalances` | < 200ms | 50 |
| `getNftsForOwner` | < 300ms | 50 |
| `getAssetTransfers` | < 500ms | 150 |
| Multi-chain portfolio | < 2s | ~400 |

## Instructions

### Step 1: Response Caching with TTL

```typescript
// src/performance/cache.ts
import { Alchemy, Network } from 'alchemy-sdk';

class BlockchainCache {
  private store = new Map<string, { data: any; expiry: number }>();

  // Different TTLs for different data freshness needs
  private TTL: Record<string, number> = {
    blockNumber: 12000,     // 12s (~1 block)
    balance: 30000,         // 30s
    tokenBalances: 60000,   // 60s
    nftOwnership: 300000,   // 5 min (NFTs transfer less frequently)
    contractMetadata: 3600000, // 1 hour (rarely changes)
    tokenMetadata: 86400000,   // 24 hours (almost never changes)
  };

  async cached<T>(category: string, key: string, fetcher: () => Promise<T>): Promise<T> {
    const cacheKey = `${category}:${key}`;
    const entry = this.store.get(cacheKey);
    if (entry && entry.expiry > Date.now()) return entry.data;

    const data = await fetcher();
    this.store.set(cacheKey, { data, expiry: Date.now() + (this.TTL[category] || 30000) });
    return data;
  }

  invalidate(category: string): void {
    for (const key of this.store.keys()) {
      if (key.startsWith(`${category}:`)) this.store.delete(key);
    }
  }
}

const cache = new BlockchainCache();
export { cache };
```

### Step 2: Parallel Multi-Chain Fetching

```typescript
// src/performance/parallel-fetch.ts
import { Alchemy, Network } from 'alchemy-sdk';
import { cache } from './cache';

const CHAINS = [
  { name: 'ethereum', network: Network.ETH_MAINNET },
  { name: 'polygon', network: Network.MATIC_MAINNET },
  { name: 'arbitrum', network: Network.ARB_MAINNET },
  { name: 'base', network: Network.BASE_MAINNET },
];

async function multiChainBalance(address: string) {
  const results = await Promise.allSettled(
    CHAINS.map(chain =>
      cache.cached('balance', `${chain.name}:${address}`, async () => {
        const client = new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: chain.network });
        const bal = await client.core.getBalance(address);
        return { chain: chain.name, balance: (parseInt(bal.toString()) / 1e18).toFixed(6) };
      })
    )
  );

  return results
    .filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled')
    .map(r => r.value);
}
```

### Step 3: Batch NFT Metadata (Reduce CU)

```typescript
// src/performance/batch-nft.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.ETH_MAINNET });

// SLOW: Individual calls = 50 CU each
// async function slowGetMetadata(tokens) {
//   return Promise.all(tokens.map(t => alchemy.nft.getNftMetadata(t.contract, t.tokenId)));
// }

// FAST: Batch call = 50 CU total for up to 100 tokens
async function fastGetMetadata(tokens: Array<{ contractAddress: string; tokenId: string }>) {
  return alchemy.nft.getNftMetadataBatch(tokens);
}
```

### Step 4: WebSocket for Real-Time Data

```typescript
// src/performance/realtime.ts
import { Alchemy, AlchemySubscription, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.ETH_MAINNET });

// Use WebSocket subscriptions instead of polling
function watchAddress(address: string, onActivity: (tx: any) => void) {
  alchemy.ws.on(
    {
      method: AlchemySubscription.PENDING_TRANSACTIONS,
      toAddress: address,
    },
    (tx) => onActivity(tx)
  );
}

// Auto-reconnect on disconnect
alchemy.ws.on('close', () => {
  console.log('WebSocket disconnected — reconnecting in 5s');
  setTimeout(() => alchemy.ws.connect(), 5000);
});
```

## Output

- TTL-based response cache matching data freshness requirements
- Parallel multi-chain fetching (4 chains in < 2s)
- Batch NFT metadata (100x CU reduction)
- WebSocket subscriptions replacing polling

## Resources

- [Alchemy Compute Units](https://www.alchemy.com/docs/reference/compute-unit-costs)
- [Alchemy WebSockets](https://www.alchemy.com/docs/reference/sdk-websockets)

## Next Steps

For cost optimization, see `alchemy-cost-tuning`.
