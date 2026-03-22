---
name: alchemy-rate-limits
description: |
  Implement Alchemy Compute Unit (CU) rate limiting and request throttling.
  Use when handling 429 errors, optimizing CU usage, or managing
  concurrent blockchain queries within plan limits.
  Trigger: "alchemy rate limit", "alchemy 429", "alchemy compute units",
  "alchemy throttling", "alchemy CU budget".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, rate-limiting]
compatible-with: claude-code
---

# Alchemy Rate Limits

## Overview

Alchemy uses Compute Units (CU) to measure API usage. Different methods cost different CU amounts. Rate limits are per-second, and exceeding them returns 429 errors.

## Compute Unit Costs

| Method | CU Cost | Category |
|--------|---------|----------|
| `eth_blockNumber` | 10 | Core |
| `eth_getBalance` | 19 | Core |
| `eth_call` | 26 | Core |
| `eth_getTransactionReceipt` | 15 | Core |
| `getTokenBalances` | 50 | Enhanced |
| `getTokenMetadata` | 50 | Enhanced |
| `getAssetTransfers` | 150 | Enhanced |
| `getNftsForOwner` | 50 | NFT |
| `getNftMetadataBatch` | 50 | NFT |
| `getContractMetadata` | 50 | NFT |

## Plan Limits

| Plan | CU/sec | Monthly CU | Price |
|------|--------|------------|-------|
| Free | 330 | 300M | $0 |
| Growth | 660 | 1.2B | $49/mo |
| Scale | Custom | Custom | Custom |

## Instructions

### Step 1: CU-Aware Request Throttler

```typescript
// src/alchemy/throttler.ts
import Bottleneck from 'bottleneck';

const CU_COSTS: Record<string, number> = {
  'eth_blockNumber': 10,
  'eth_getBalance': 19,
  'eth_call': 26,
  'getTokenBalances': 50,
  'getAssetTransfers': 150,
  'getNftsForOwner': 50,
};

// Free tier: 330 CU/sec = ~16 getBalance calls/sec
const limiter = new Bottleneck({
  reservoir: 330,                    // CU budget per interval
  reservoirRefreshInterval: 1000,    // Refresh every second
  reservoirRefreshAmount: 330,       // Reset to max CU/sec
  maxConcurrent: 10,                 // Max parallel requests
  minTime: 50,                       // Min 50ms between requests
});

limiter.on('depleted', () => {
  console.warn('CU budget depleted — queueing requests');
});

async function throttledAlchemyCall<T>(
  method: string,
  operation: () => Promise<T>,
): Promise<T> {
  const cost = CU_COSTS[method] || 26; // Default to eth_call cost
  return limiter.schedule({ weight: cost }, operation);
}

export { throttledAlchemyCall, limiter };
```

### Step 2: Batch Optimizer

```typescript
// src/alchemy/batch-optimizer.ts
import { Alchemy } from 'alchemy-sdk';

// Instead of N individual calls, batch when possible
async function batchGetBalances(
  alchemy: Alchemy,
  addresses: string[],
): Promise<Map<string, string>> {
  const results = new Map<string, string>();

  // Process in chunks to stay under rate limit
  const CHUNK_SIZE = 10;
  for (let i = 0; i < addresses.length; i += CHUNK_SIZE) {
    const chunk = addresses.slice(i, i + CHUNK_SIZE);
    const balances = await Promise.all(
      chunk.map(addr => alchemy.core.getBalance(addr))
    );
    chunk.forEach((addr, idx) => {
      results.set(addr, (parseInt(balances[idx].toString()) / 1e18).toFixed(6));
    });

    // Pause between chunks to stay under CU limit
    if (i + CHUNK_SIZE < addresses.length) {
      await new Promise(r => setTimeout(r, 200));
    }
  }

  return results;
}

export { batchGetBalances };
```

### Step 3: 429 Retry Handler

```typescript
// src/alchemy/retry.ts
async function withAlchemyRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 5,
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      if (err.response?.status !== 429 || attempt === maxRetries) throw err;

      const retryAfter = parseInt(err.response.headers?.['retry-after'] || '1');
      const jitter = Math.random() * 500;
      const delay = retryAfter * 1000 + jitter;

      console.log(`Rate limited — retry ${attempt}/${maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Output

- CU-aware Bottleneck throttler matching plan limits
- Batch optimizer reducing total CU consumption
- 429 retry handler with Retry-After header support

## Resources

- [Alchemy Rate Limits](https://www.alchemy.com/docs/reference/rate-limits)
- [Alchemy Compute Units](https://www.alchemy.com/docs/reference/compute-unit-costs)
- [Bottleneck npm](https://www.npmjs.com/package/bottleneck)

## Next Steps

For security best practices, see `alchemy-security-basics`.
