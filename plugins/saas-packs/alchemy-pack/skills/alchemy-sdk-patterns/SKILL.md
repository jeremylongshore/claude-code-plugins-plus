---
name: alchemy-sdk-patterns
description: |
  Apply production-ready Alchemy SDK patterns for Web3 applications.
  Use when building reusable blockchain clients, implementing caching,
  multi-chain abstractions, or type-safe contract interactions.
  Trigger: "alchemy SDK patterns", "alchemy best practices", "alchemy code patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, patterns]
compatible-with: claude-code
---

# Alchemy SDK Patterns

## Overview

Production patterns for the `alchemy-sdk` package: singleton clients, multi-chain factories, response caching, and type-safe contract wrappers.

## Instructions

### Step 1: Multi-Chain Client Factory

```typescript
// src/alchemy/client-factory.ts
import { Alchemy, Network } from 'alchemy-sdk';

type ChainName = 'ethereum' | 'polygon' | 'arbitrum' | 'optimism' | 'base';

const NETWORK_MAP: Record<ChainName, Network> = {
  ethereum: Network.ETH_MAINNET,
  polygon: Network.MATIC_MAINNET,
  arbitrum: Network.ARB_MAINNET,
  optimism: Network.OPT_MAINNET,
  base: Network.BASE_MAINNET,
};

class AlchemyClientFactory {
  private static clients = new Map<string, Alchemy>();

  static getClient(chain: ChainName): Alchemy {
    if (!this.clients.has(chain)) {
      this.clients.set(chain, new Alchemy({
        apiKey: process.env.ALCHEMY_API_KEY,
        network: NETWORK_MAP[chain],
        maxRetries: 3,
      }));
    }
    return this.clients.get(chain)!;
  }

  static getAllClients(): Map<ChainName, Alchemy> {
    for (const chain of Object.keys(NETWORK_MAP) as ChainName[]) {
      this.getClient(chain);
    }
    return this.clients as Map<ChainName, Alchemy>;
  }
}

export { AlchemyClientFactory, ChainName };
```

### Step 2: Response Caching Layer

```typescript
// src/alchemy/cache.ts
interface CacheEntry<T> { data: T; expiresAt: number; }

class AlchemyCache {
  private cache = new Map<string, CacheEntry<any>>();
  private defaultTtlMs: number;

  constructor(defaultTtlMs: number = 30000) { // 30s default
    this.defaultTtlMs = defaultTtlMs;
  }

  async getOrFetch<T>(key: string, fetcher: () => Promise<T>, ttlMs?: number): Promise<T> {
    const cached = this.cache.get(key);
    if (cached && cached.expiresAt > Date.now()) return cached.data;

    const data = await fetcher();
    this.cache.set(key, { data, expiresAt: Date.now() + (ttlMs || this.defaultTtlMs) });
    return data;
  }

  invalidate(keyPrefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(keyPrefix)) this.cache.delete(key);
    }
  }
}

// Usage with Alchemy
const cache = new AlchemyCache();

async function getCachedBalance(alchemy: Alchemy, address: string): Promise<string> {
  return cache.getOrFetch(
    `balance:${address}`,
    async () => {
      const balance = await alchemy.core.getBalance(address);
      return (parseInt(balance.toString()) / 1e18).toFixed(6);
    },
    15000 // 15s cache for balances
  );
}

export { AlchemyCache, getCachedBalance };
```

### Step 3: Typed NFT Query Builder

```typescript
// src/alchemy/nft-query.ts
import { Alchemy, NftOrdering } from 'alchemy-sdk';

class NftQueryBuilder {
  private alchemy: Alchemy;
  private _owner?: string;
  private _contracts: string[] = [];
  private _pageSize = 20;
  private _excludeFilters: string[] = [];

  constructor(alchemy: Alchemy) { this.alchemy = alchemy; }

  forOwner(address: string): this { this._owner = address; return this; }
  inCollection(contractAddress: string): this { this._contracts.push(contractAddress); return this; }
  pageSize(size: number): this { this._pageSize = size; return this; }
  excludeSpam(): this { this._excludeFilters.push('SPAM'); return this; }

  async execute() {
    if (!this._owner) throw new Error('Owner address required');

    return this.alchemy.nft.getNftsForOwner(this._owner, {
      contractAddresses: this._contracts.length > 0 ? this._contracts : undefined,
      pageSize: this._pageSize,
      excludeFilters: this._excludeFilters as any[],
    });
  }
}

// Usage:
// const nfts = await new NftQueryBuilder(alchemy)
//   .forOwner('vitalik.eth')
//   .excludeSpam()
//   .pageSize(50)
//   .execute();
```

### Step 4: Error Classification

```typescript
// src/alchemy/errors.ts
type AlchemyErrorType = 'rate_limit' | 'auth' | 'network' | 'invalid_params' | 'server' | 'unknown';

function classifyError(error: any): { type: AlchemyErrorType; retryable: boolean; message: string } {
  const status = error.response?.status || error.code;

  if (status === 429) return { type: 'rate_limit', retryable: true, message: 'Rate limit exceeded' };
  if (status === 401 || status === 403) return { type: 'auth', retryable: false, message: 'Invalid API key' };
  if (status >= 500) return { type: 'server', retryable: true, message: 'Alchemy server error' };
  if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') return { type: 'network', retryable: true, message: 'Network error' };
  if (error.message?.includes('invalid params')) return { type: 'invalid_params', retryable: false, message: error.message };
  return { type: 'unknown', retryable: false, message: error.message };
}

export { classifyError, AlchemyErrorType };
```

## Output

- Multi-chain client factory with lazy initialization
- Response cache with configurable TTL
- Type-safe NFT query builder pattern
- Structured error classification for retry decisions

## Resources

- [Alchemy SDK GitHub](https://github.com/alchemyplatform/alchemy-sdk-js)
- [Alchemy Docs](https://www.alchemy.com/docs)

## Next Steps

Apply patterns in `alchemy-core-workflow-a` for real portfolio tracking.
