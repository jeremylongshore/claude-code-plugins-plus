---
name: alchemy-cost-tuning
description: |
  Optimize Alchemy API costs through CU budgeting, caching, and plan selection.
  Use when analyzing Alchemy billing, reducing Compute Unit consumption,
  or choosing the right plan for your dApp traffic.
  Trigger: "alchemy cost", "alchemy pricing", "alchemy CU budget",
  "alchemy billing optimization", "alchemy free tier limits".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, cost-optimization]
compatible-with: claude-code
---

# Alchemy Cost Tuning

## Overview

Alchemy pricing is based on Compute Units (CU). Different API methods have different CU costs. Optimize by caching, batching, choosing cheaper methods, and right-sizing your plan.

## Plan Comparison

| Plan | CU/sec | Monthly CU | Price | Best For |
|------|--------|------------|-------|----------|
| Free | 330 | 300M | $0 | Dev/prototyping |
| Growth | 660 | 1.2B | $49/mo | Small dApps |
| Scale | Custom | Custom | Custom | High-traffic apps |

## CU Cost Reference (Top Methods)

| Method | CU | Optimization |
|--------|-----|-------------|
| `eth_blockNumber` | 10 | Cache 12s (1 block) |
| `eth_getBalance` | 19 | Cache 30s |
| `eth_call` | 26 | Cache based on use case |
| `getTokenBalances` | 50 | Cache 60s; batch addresses |
| `getNftsForOwner` | 50 | Cache 5 min |
| `getTokenMetadata` | 50 | Cache 24h (rarely changes) |
| `getAssetTransfers` | 150 | Cache aggressively; paginate |
| `getNftMetadataBatch` | 50 | Use batch over individual calls |

## Instructions

### Step 1: CU Usage Monitor

```typescript
// src/cost/cu-monitor.ts
const CU_COSTS: Record<string, number> = {
  'eth_blockNumber': 10, 'eth_getBalance': 19, 'eth_call': 26,
  'getTokenBalances': 50, 'getNftsForOwner': 50, 'getTokenMetadata': 50,
  'getAssetTransfers': 150, 'getNftMetadataBatch': 50,
};

class CuMonitor {
  private usage: Array<{ method: string; cu: number; timestamp: number }> = [];

  record(method: string): void {
    this.usage.push({ method, cu: CU_COSTS[method] || 26, timestamp: Date.now() });
  }

  getHourlyReport(): { totalCu: number; byMethod: Record<string, number> } {
    const cutoff = Date.now() - 3600000;
    const recent = this.usage.filter(u => u.timestamp > cutoff);
    const byMethod: Record<string, number> = {};
    let totalCu = 0;

    for (const u of recent) {
      byMethod[u.method] = (byMethod[u.method] || 0) + u.cu;
      totalCu += u.cu;
    }

    return { totalCu, byMethod };
  }

  getMonthlyProjection(): { projectedMonthly: number; planRecommendation: string } {
    const hourly = this.getHourlyReport();
    const projectedMonthly = hourly.totalCu * 24 * 30;

    let recommendation = 'Free';
    if (projectedMonthly > 300_000_000) recommendation = 'Growth';
    if (projectedMonthly > 1_200_000_000) recommendation = 'Scale';

    return { projectedMonthly, planRecommendation: recommendation };
  }
}

export { CuMonitor };
```

### Step 2: Cost-Optimized Client Wrapper

```typescript
// src/cost/optimized-client.ts
import { Alchemy, Network } from 'alchemy-sdk';

const cache = new Map<string, { data: any; expiry: number }>();

// Cache token metadata aggressively (rarely changes)
async function getTokenMetadataCached(alchemy: Alchemy, contract: string) {
  const key = `metadata:${contract}`;
  const cached = cache.get(key);
  if (cached && cached.expiry > Date.now()) return cached.data;

  const data = await alchemy.core.getTokenMetadata(contract);
  cache.set(key, { data, expiry: Date.now() + 86400000 }); // 24h cache
  return data;
}

// Use batch instead of individual NFT metadata calls
// 1 batch call (50 CU) vs 100 individual calls (5000 CU)
async function getNftMetadataOptimized(
  alchemy: Alchemy,
  tokens: Array<{ contractAddress: string; tokenId: string }>
) {
  const BATCH_SIZE = 100;
  const results = [];
  for (let i = 0; i < tokens.length; i += BATCH_SIZE) {
    const batch = tokens.slice(i, i + BATCH_SIZE);
    const batchResults = await alchemy.nft.getNftMetadataBatch(batch);
    results.push(...batchResults);
  }
  return results;
}
```

### Step 3: Free Tier Optimization Checklist

```typescript
// For staying within Free tier (330 CU/sec, 300M CU/month):
// 1. Cache eth_blockNumber (saves 10 CU per redundant call)
// 2. Cache token metadata (saves 50 CU per redundant call)
// 3. Use getNftMetadataBatch instead of getNftMetadata (100x savings)
// 4. Avoid getAssetTransfers loops (150 CU each — cache results)
// 5. Use WebSockets instead of polling (one connection vs repeated calls)
// 6. Rate-limit user-facing endpoints to prevent CU bursts
```

## Output

- CU usage monitor with hourly reports and plan projections
- Cost-optimized client with aggressive caching
- Batch operations reducing CU consumption by 100x
- Free tier optimization checklist

## Resources

- [Alchemy Pricing](https://www.alchemy.com/pricing)
- [Alchemy Compute Units](https://www.alchemy.com/docs/reference/compute-unit-costs)

## Next Steps

For architecture design, see `alchemy-reference-architecture`.
