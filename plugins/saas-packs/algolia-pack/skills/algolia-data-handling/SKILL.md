---
name: algolia-data-handling
description: |
  Implement Algolia data handling: record transforms, PII filtering before indexing,
  data retention, GDPR/CCPA compliance with Algolia's deleteByQuery and Insights deletion.
  Trigger: "algolia data", "algolia PII", "algolia GDPR", "algolia data retention",
  "algolia privacy", "algolia CCPA", "algolia data sync".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Data Handling

## Overview

Algolia stores your records in their cloud. You control what data goes in (via `saveObjects`), what comes back (via `attributesToRetrieve`), and what users can search (via `searchableAttributes`). For privacy compliance, you must filter PII before indexing and implement deletion workflows.

## Data Flow: Source → Algolia → User

```
Source Database        Transform           Algolia Index           Search Response
┌──────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Full user │     │ Strip PII    │     │ Searchable       │     │ Retrieved    │
│ record    │ ──▶ │ Truncate     │ ──▶ │ fields only      │ ──▶ │ fields only  │
│ (all cols)│     │ Normalize    │     │ + ranking data   │     │ (UI needs)   │
└──────────┘     └──────────────┘     └──────────────────┘     └──────────────┘
```

## Instructions

### Step 1: Transform Records Before Indexing

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// Define what goes into Algolia — NOT everything from your DB
interface AlgoliaProduct {
  objectID: string;
  name: string;
  description: string;     // Truncated, plain text
  category: string;
  brand: string;
  price: number;
  in_stock: boolean;
  image_url: string;
  rating: number;
  _tags: string[];
}

function transformForAlgolia(dbRecord: any): AlgoliaProduct {
  return {
    objectID: dbRecord.id,
    name: dbRecord.name,
    description: stripHtml(dbRecord.description).substring(0, 5000),
    category: dbRecord.category?.name || 'uncategorized',
    brand: dbRecord.brand?.name || '',
    price: dbRecord.price_cents / 100,
    in_stock: dbRecord.inventory_count > 0,
    image_url: dbRecord.images?.[0]?.url || '',
    rating: dbRecord.avg_rating || 0,
    _tags: buildTags(dbRecord),
  };
}

// Strip HTML tags for clean search text
function stripHtml(html: string): string {
  return html?.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim() || '';
}

function buildTags(record: any): string[] {
  const tags: string[] = [];
  if (record.is_featured) tags.push('featured');
  if (record.is_new) tags.push('new-arrival');
  if (record.discount_percent > 0) tags.push('on-sale');
  return tags;
}
```

### Step 2: PII Detection and Filtering

```typescript
// NEVER index PII unless absolutely necessary for search
const PII_FIELDS = ['email', 'phone', 'ssn', 'address', 'credit_card', 'password', 'api_key'];

function stripPII(record: Record<string, any>): Record<string, any> {
  const clean = { ...record };
  for (const field of PII_FIELDS) {
    delete clean[field];
  }
  return clean;
}

// If you MUST index user-facing names (e.g., author names in articles)
// Use unretrievableAttributes so they're searchable but never returned
await client.setSettings({
  indexName: 'articles',
  indexSettings: {
    searchableAttributes: ['title', 'author_name', 'content'],
    unretrievableAttributes: ['author_name'],  // Searchable but never in response
    attributesToRetrieve: ['title', 'excerpt', 'url', 'published_at'],
  },
});
```

### Step 3: Algolia-Side Data Access Control

```typescript
// Use secured API keys to filter what each user can see
function generateUserKey(userId: string, tenantId: string) {
  return client.generateSecuredApiKey({
    parentApiKey: process.env.ALGOLIA_SEARCH_KEY!,
    restrictions: {
      filters: `tenant_id:${tenantId} AND (visibility:public OR created_by:${userId})`,
      validUntil: Math.floor(Date.now() / 1000) + 3600,
    },
  });
}

// User can only search records where:
// - tenant_id matches their org AND
// - visibility is public OR they created it
```

### Step 4: GDPR Right to Deletion

```typescript
// When a user requests data deletion:
async function deleteUserData(userId: string) {
  const results: Record<string, string> = {};

  // 1. Delete user's records from all indices
  for (const indexName of ['products', 'reviews', 'wishlists']) {
    try {
      await client.deleteBy({
        indexName,
        deleteByParams: { filters: `created_by:${userId}` },
      });
      results[indexName] = 'deleted';
    } catch (e) {
      results[indexName] = `failed: ${e}`;
    }
  }

  // 2. Delete Insights/Analytics data for this user
  // Algolia retains events for 90 days by default
  // Use the Insights API to request user data deletion
  await client.deleteUserToken({ userToken: userId });

  // 3. Log the deletion for compliance audit
  console.log({
    event: 'gdpr.deletion',
    userId,
    timestamp: new Date().toISOString(),
    results,
  });

  return results;
}
```

### Step 5: Data Subject Access Request (DSAR)

```typescript
// Export all data associated with a user
async function exportUserData(userId: string) {
  const exportData: Record<string, any[]> = {};

  for (const indexName of ['products', 'reviews', 'wishlists']) {
    const records: any[] = [];
    let cursor: string | undefined;

    // Browse all records matching the user
    do {
      const result = await client.browse({
        indexName,
        browseParams: {
          filters: `created_by:${userId}`,
          hitsPerPage: 1000,
          cursor,
        },
      });
      records.push(...result.hits);
      cursor = result.cursor;
    } while (cursor);

    exportData[indexName] = records;
  }

  return {
    exportedAt: new Date().toISOString(),
    userId,
    data: exportData,
  };
}
```

### Step 6: Data Retention and Cleanup

```typescript
// Scheduled job: delete old records past retention period
async function enforceRetention(indexName: string, retentionDays: number) {
  const cutoffTimestamp = Math.floor(
    (Date.now() - retentionDays * 24 * 60 * 60 * 1000) / 1000
  );

  await client.deleteBy({
    indexName,
    deleteByParams: {
      filters: `created_at_timestamp < ${cutoffTimestamp}`,
    },
  });

  console.log(`Deleted records older than ${retentionDays} days from ${indexName}`);
}

// Run daily: enforceRetention('activity_logs', 90);
```

## Data Classification for Algolia

| Category | Examples | Index It? | Retrieve It? |
|----------|----------|-----------|-------------|
| Public product data | Name, price, category | Yes | Yes |
| Searchable metadata | Tags, internal categories | Yes | No (`unretrievableAttributes`) |
| User-generated content | Reviews, comments | Yes (anonymized) | Yes |
| PII | Email, phone, address | NO | NO |
| Sensitive business data | Margins, supplier costs | NO | NO |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII in Algolia index | Transform didn't strip | Add PII check to indexing pipeline |
| `deleteBy` no effect | Filter doesn't match | Verify field is in `attributesForFaceting` |
| DSAR export incomplete | Paginated results | Use cursor-based browsing |
| Retention job deletes too much | Wrong timestamp format | Use Unix timestamp (seconds), not milliseconds |

## Resources

- [Algolia Privacy & GDPR](https://www.algolia.com/policies/privacy/)
- [deleteBy Reference](https://www.algolia.com/doc/api-reference/api-methods/delete-by/)
- [browse Reference](https://www.algolia.com/doc/api-reference/api-methods/browse/)
- [Insights User Deletion](https://www.algolia.com/doc/guides/sending-events/getting-started/)

## Next Steps

For enterprise access control, see `algolia-enterprise-rbac`.
