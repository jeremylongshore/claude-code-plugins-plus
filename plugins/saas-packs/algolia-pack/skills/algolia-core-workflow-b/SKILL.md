---
name: algolia-core-workflow-b
description: |
  Implement Algolia indexing pipeline: data sync, partial updates, synonyms, and rules.
  The secondary money-path workflow: keep your index in sync with source data.
  Trigger: "algolia indexing", "sync data to algolia", "algolia synonyms",
  "algolia rules", "algolia partial update", "algolia reindex".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Core Workflow B — Indexing & Data Sync

## Overview

Keep your Algolia index synchronized with your source database. Covers full reindex, incremental updates, partial updates, synonyms, and query rules.

## Prerequisites

- Completed `algolia-install-auth` setup
- Familiarity with `algolia-core-workflow-a` (search)
- Source database or API with change tracking (timestamps, events)

## Instructions

### Step 1: Full Reindex with replaceAllObjects

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// replaceAllObjects atomically swaps index content
// Internally: creates temp index → indexes all records → moves temp to target
// Search continues on old data until swap is complete — zero downtime
async function fullReindex(records: Record<string, any>[]) {
  const { taskID } = await client.replaceAllObjects({
    indexName: 'products',
    objects: records,
    batchSize: 1000,  // Records per batch (default 1000)
  });
  await client.waitForTask({ indexName: 'products', taskID });
  console.log(`Full reindex complete: ${records.length} records`);
}
```

### Step 2: Incremental Updates with partialUpdateObject

```typescript
// Only update changed fields — much faster than full saveObjects
async function updateProductPrice(objectID: string, newPrice: number) {
  await client.partialUpdateObject({
    indexName: 'products',
    objectID,
    attributesToUpdate: {
      price: newPrice,
      updated_at: new Date().toISOString(),
    },
    createIfNotExists: false,  // Don't create if missing
  });
}

// Batch partial updates
async function syncPriceChanges(changes: { id: string; price: number }[]) {
  const { taskID } = await client.partialUpdateObjects({
    indexName: 'products',
    objects: changes.map(c => ({
      objectID: c.id,
      price: c.price,
      updated_at: new Date().toISOString(),
    })),
    createIfNotExists: false,
  });
  await client.waitForTask({ indexName: 'products', taskID });
}
```

### Step 3: Manage Synonyms

```typescript
// Synonyms help users find products with different terminology
await client.saveSynonyms({
  indexName: 'products',
  synonymHit: [
    // Two-way synonym: any of these terms match each other
    {
      objectID: 'syn-1',
      type: 'synonym',
      synonyms: ['laptop', 'notebook', 'portable computer'],
    },
    // One-way synonym: "phone" also searches for "smartphone" but not reverse
    {
      objectID: 'syn-2',
      type: 'oneWaySynonym',
      input: 'phone',
      synonyms: ['smartphone', 'mobile phone', 'cell phone'],
    },
    // Alt correction: minor typos/variations
    {
      objectID: 'syn-3',
      type: 'altCorrection1',
      word: 'color',
      corrections: ['colour'],
    },
    // Placeholder: replace pattern with alternatives
    {
      objectID: 'syn-4',
      type: 'placeholder',
      placeholder: '<size>',
      replacements: ['small', 'medium', 'large', 'XL'],
    },
  ],
  forwardToReplicas: true,
  replaceExistingSynonyms: false,  // true = wipe existing first
});
```

### Step 4: Configure Query Rules

```typescript
// Rules let you pin, hide, boost, or filter results for specific queries
await client.saveRule({
  indexName: 'products',
  objectID: 'rule-sale-banner',
  rule: {
    conditions: [{
      anchoring: 'contains',
      pattern: 'sale',
    }],
    consequence: {
      // Pin a specific record to position 1
      promote: [{ objectID: 'promo-banner-sale', position: 0 }],

      // Add automatic filter
      params: {
        filters: 'on_sale = true',
      },
    },
    description: 'When user searches "sale", filter to sale items and pin banner',
    enabled: true,
  },
});

// Hide a product from search results
await client.saveRule({
  indexName: 'products',
  objectID: 'rule-hide-discontinued',
  rule: {
    conditions: [{ anchoring: 'is', pattern: '' }],  // Matches all queries
    consequence: {
      hide: [{ objectID: 'discontinued-product-123' }],
    },
    description: 'Hide discontinued product from all searches',
    enabled: true,
  },
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Record is too big (limit: 10KB)` | Object exceeds free-tier limit | Strip unnecessary fields; paid plans allow 100KB |
| `Synonym already exists` | Duplicate objectID | Use `replaceExistingSynonyms: true` or unique IDs |
| `Invalid rule condition` | Wrong `anchoring` value | Use `is`, `startsWith`, `endsWith`, or `contains` |
| Partial update creates new record | `createIfNotExists` default is `true` | Set `createIfNotExists: false` |

## Examples

### Database Change Listener → Algolia Sync

```typescript
// Listen for DB changes and push to Algolia
import { getClient } from './algolia/client';

async function onDatabaseChange(event: { type: string; record: any }) {
  const client = getClient();
  const idx = 'products';

  switch (event.type) {
    case 'INSERT':
    case 'UPDATE':
      await client.saveObject({ indexName: idx, body: event.record });
      break;
    case 'DELETE':
      await client.deleteObject({ indexName: idx, objectID: event.record.id });
      break;
  }
}
```

### Search for Synonyms

```typescript
// List all synonyms matching a query
const { hits } = await client.searchSynonyms({
  indexName: 'products',
  searchSynonymsParams: { query: 'phone', type: 'synonym' },
});
console.log(`Found ${hits.length} synonym sets matching "phone"`);
```

## Resources

- [Indexing Guide](https://www.algolia.com/doc/guides/sending-and-managing-data/send-and-update-your-data/)
- [Synonyms Guide](https://www.algolia.com/doc/guides/managing-results/optimize-search-results/adding-synonyms/)
- [Rules Guide](https://www.algolia.com/doc/guides/managing-results/rules/rules-overview/)
- [replaceAllObjects Reference](https://www.algolia.com/doc/api-reference/api-methods/replace-all-objects/)

## Next Steps

For common errors, see `algolia-common-errors`.
