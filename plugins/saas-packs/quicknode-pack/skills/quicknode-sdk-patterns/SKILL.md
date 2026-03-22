---
name: quicknode-sdk-patterns
description: |
  Production-ready QuickNode SDK and ethers.js patterns for blockchain applications.
  Use when building production dApps, implementing retry logic, or establishing patterns.
  Trigger with phrases like "quicknode patterns", "ethers best practices", "web3 patterns".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, quicknode, blockchain, web3, patterns]
compatible-with: claude-code, codex, openclaw
---

# QuickNode SDK Patterns

## Overview
Production-ready patterns for blockchain development with QuickNode: provider singletons, retry logic, batch RPC calls, and multi-chain support.

## Prerequisites
- Completed `quicknode-install-auth`
- ethers.js or @quicknode/sdk installed

## Instructions

### Step 1: Provider Singleton
```typescript
import { ethers } from 'ethers';

let _provider: ethers.JsonRpcProvider | null = null;

export function getProvider(): ethers.JsonRpcProvider {
  if (!_provider) {
    _provider = new ethers.JsonRpcProvider(process.env.QUICKNODE_ENDPOINT, undefined, {
      staticNetwork: true,  // Skip chainId lookup on every call
      batchMaxCount: 10,    // Enable batch RPC
    });
  }
  return _provider;
}
```

### Step 2: Retry Wrapper with Backoff
```typescript
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      const isRetryable = err.code === 'SERVER_ERROR' || err.code === 'TIMEOUT' || err.status === 429;
      if (!isRetryable || attempt === maxRetries) throw err;
      const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}

// Usage
const balance = await withRetry(() => getProvider().getBalance(address));
```

### Step 3: Multi-Chain Client Factory
```typescript
const ENDPOINTS: Record<string, string> = {
  ethereum: process.env.QUICKNODE_ETH_ENDPOINT!,
  polygon: process.env.QUICKNODE_POLYGON_ENDPOINT!,
  arbitrum: process.env.QUICKNODE_ARB_ENDPOINT!,
};

const providers = new Map<string, ethers.JsonRpcProvider>();

export function getChainProvider(chain: string): ethers.JsonRpcProvider {
  if (!providers.has(chain)) {
    const url = ENDPOINTS[chain];
    if (!url) throw new Error(`No endpoint for chain: ${chain}`);
    providers.set(chain, new ethers.JsonRpcProvider(url, undefined, { staticNetwork: true }));
  }
  return providers.get(chain)!;
}
```

### Step 4: Batch RPC Calls
```typescript
async function batchGetBalances(addresses: string[]): Promise<Map<string, bigint>> {
  const provider = getProvider();
  const results = new Map<string, bigint>();

  // ethers.js batches these automatically when batchMaxCount > 1
  const promises = addresses.map(async (addr) => {
    const balance = await provider.getBalance(addr);
    results.set(addr, balance);
  });

  await Promise.all(promises);
  return results;
}
```

### Step 5: Contract Wrapper with Caching
```typescript
import { LRUCache } from 'lru-cache';

const contractCache = new LRUCache<string, any>({ max: 100, ttl: 60000 });

async function cachedContractCall(contract: ethers.Contract, method: string, ...args: any[]) {
  const key = `${contract.target}:${method}:${JSON.stringify(args)}`;
  const cached = contractCache.get(key);
  if (cached) return cached;

  const result = await contract[method](...args);
  contractCache.set(key, result);
  return result;
}
```

## Output
- Thread-safe provider singleton with batch support
- Retry logic for transient RPC failures
- Multi-chain client factory
- Cached contract calls reducing RPC usage

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | All RPC calls | One connection, reused |
| Retry wrapper | Transient failures | Automatic recovery |
| Multi-chain factory | Cross-chain dApps | Clean chain switching |
| Contract cache | Repeated reads | Fewer RPC calls |

## Resources
- [QuickNode SDK](https://www.quicknode.com/docs/quicknode-sdk/getting-started)
- [ethers.js Documentation](https://docs.ethers.org/)

## Next Steps
Build transaction workflows: `quicknode-core-workflow-a`
