---
name: framer-cost-tuning
description: |
  Optimize Framer costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Framer billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "framer cost", "framer billing",
  "reduce framer costs", "framer pricing", "framer expensive", "framer budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Cost Tuning

## Overview

Optimize Framer costs across plans and features. The Server API is free during beta. Main costs are Framer site plans, custom domains, and team seats.

## Framer Plans

| Plan | Price | CMS Items | Custom Domain | Pages |
|------|-------|-----------|---------------|-------|
| Free | $0 | 100 | No | 2 |
| Mini | $5/mo | 200 | Yes | 150 |
| Basic | $15/mo | 1,000 | Yes | 300 |
| Pro | $30/mo | 10,000 | Yes | Unlimited |
| Enterprise | Custom | Unlimited | Yes | Unlimited |

## Cost Optimization Strategies

### Step 1: CMS Item Budgeting

```typescript
// Track CMS item usage to avoid plan overages
async function checkCMSUsage(client: any) {
  const collections = await client.getCollections();
  let totalItems = 0;
  for (const col of collections) {
    const items = await col.getItems();
    totalItems += items.length;
    console.log(`${col.name}: ${items.length} items`);
  }
  console.log(`Total CMS items: ${totalItems}`);
  // Pro plan: 10,000 limit
  console.log(`Usage: ${((totalItems / 10000) * 100).toFixed(1)}% of Pro limit`);
}
```

### Step 2: Minimize Publish Frequency

```typescript
// Batch CMS updates before publishing (each publish rebuilds the site)
async function batchUpdateAndPublish(updates: Array<{ collection: string; items: any[] }>) {
  const client = await getClient();
  for (const update of updates) {
    const col = (await client.getCollections()).find(c => c.name === update.collection);
    if (col) await col.setItems(update.items);
  }
  // Single publish after all updates
  await client.publish();
}
```

### Step 3: Development vs Production Sites

Use a free plan site for development and testing. Only pay for the production site.

## Resources

- [Framer Pricing](https://www.framer.com/pricing/)
- [Server API (Free Beta)](https://www.framer.com/developers/server-api-introduction)

## Next Steps

For architecture patterns, see `framer-reference-architecture`.
