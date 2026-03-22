---
name: webflow-hello-world
description: |
  Create a minimal working Webflow Data API v2 example.
  Use when starting a new Webflow integration, testing your setup,
  or learning basic Webflow API patterns — list sites, read CMS collections, create items.
  Trigger with phrases like "webflow hello world", "webflow example",
  "webflow quick start", "simple webflow code", "first webflow API call".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Hello World

## Overview

Minimal working examples demonstrating the three core Webflow Data API v2 operations:
listing sites, reading CMS collections/items, and creating a CMS item.

## Prerequisites

- Completed `webflow-install-auth` setup
- `webflow-api` package installed
- Valid API token with `sites:read` and `cms:read` scopes

## Instructions

### Step 1: List Your Sites

Every Webflow API call starts with a `site_id`. List your sites to find it:

```typescript
// hello-webflow.ts
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

async function listSites() {
  const { sites } = await webflow.sites.list();

  for (const site of sites!) {
    console.log(`${site.displayName}`);
    console.log(`  ID: ${site.id}`);
    console.log(`  Short name: ${site.shortName}`);
    console.log(`  Custom domains: ${site.customDomains?.map(d => d.url).join(", ")}`);
    console.log(`  Last published: ${site.lastPublished}`);
    console.log(`  Locales: ${site.locales?.map(l => l.displayName).join(", ")}`);
  }
}

listSites().catch(console.error);
```

### Step 2: List CMS Collections

Collections define your content types (blog posts, team members, products, etc.):

```typescript
async function listCollections(siteId: string) {
  const { collections } = await webflow.collections.list(siteId);

  for (const col of collections!) {
    console.log(`Collection: ${col.displayName}`);
    console.log(`  ID: ${col.id}`);
    console.log(`  Slug: ${col.slug}`);
    console.log(`  Item count: ${col.itemCount}`);
    console.log(`  Fields:`);
    for (const field of col.fields || []) {
      console.log(`    - ${field.displayName} (${field.type}, required: ${field.isRequired})`);
    }
  }
}

// Usage: pass your site_id
listCollections("your-site-id").catch(console.error);
```

### Step 3: Read CMS Items

Fetch items from a collection — staged (draft) or live (published):

```typescript
async function readItems(collectionId: string) {
  // Get staged (draft + published) items
  const { items } = await webflow.collections.items.listItems(collectionId, {
    limit: 10,
    offset: 0,
  });

  for (const item of items!) {
    console.log(`Item: ${item.fieldData?.name || item.id}`);
    console.log(`  ID: ${item.id}`);
    console.log(`  Slug: ${item.fieldData?.slug}`);
    console.log(`  Draft: ${item.isDraft}`);
    console.log(`  Archived: ${item.isArchived}`);
    console.log(`  Created: ${item.createdOn}`);
  }

  // Get live (published) items only
  const live = await webflow.collections.items.listItemsLive(collectionId, {
    limit: 10,
  });
  console.log(`\nLive items: ${live.items?.length}`);
}
```

### Step 4: Create a CMS Item

```typescript
async function createBlogPost(collectionId: string) {
  // Items are created as drafts by default (isDraft: true)
  const item = await webflow.collections.items.createItem(collectionId, {
    fieldData: {
      name: "Hello from the API",
      slug: "hello-from-api",
      // Field names must match your collection schema
      // Use the slug version of field names (lowercase, hyphens)
      "post-body": "<p>This post was created via the Webflow Data API v2.</p>",
      "author": "API Bot",
      "published-date": new Date().toISOString(),
    },
    isDraft: false, // Set false to stage for publishing
  });

  console.log(`Created item: ${item.id}`);
  console.log(`  Draft: ${item.isDraft}`);
  console.log(`  Slug: ${item.fieldData?.slug}`);

  return item;
}
```

### Step 5: Complete Hello World Script

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

async function main() {
  // 1. Get first site
  const { sites } = await webflow.sites.list();
  const site = sites![0];
  console.log(`Using site: ${site.displayName} (${site.id})\n`);

  // 2. List collections
  const { collections } = await webflow.collections.list(site.id!);
  console.log(`Found ${collections!.length} collections:`);
  for (const col of collections!) {
    console.log(`  - ${col.displayName} (${col.itemCount} items)`);
  }

  // 3. Read items from first collection
  if (collections!.length > 0) {
    const firstCol = collections![0];
    const { items } = await webflow.collections.items.listItems(firstCol.id!, {
      limit: 5,
    });
    console.log(`\nFirst ${items!.length} items in "${firstCol.displayName}":`);
    for (const item of items!) {
      console.log(`  - ${item.fieldData?.name} (${item.id})`);
    }
  }

  console.log("\nWebflow connection verified successfully.");
}

main().catch(console.error);
```

Run it:

```bash
npx tsx hello-webflow.ts
```

## Output

- Console listing of all accessible sites with IDs
- Collection schemas with field types
- CMS item data (draft and live)
- Success confirmation: `Webflow connection verified successfully.`

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Bad token | Re-check token at developers.webflow.com |
| `403 Forbidden` | Missing `cms:read` scope | Add scope to token or app |
| `404 Not Found` | Wrong `site_id` or `collection_id` | List sites first to get valid IDs |
| `429 Too Many Requests` | Rate limited | Wait 60s (Retry-After header) |
| Empty `sites` array | Token has no site access | Check workspace token permissions |

## Key Concepts

- **site_id**: Every API call is scoped to a site. Get it from `sites.list()`.
- **collection_id**: CMS collections hold typed content. Get IDs from `collections.list(siteId)`.
- **fieldData**: Item fields use the slug form of field names (e.g., `post-body`, not `Post Body`).
- **isDraft**: New items default to `isDraft: true`. Set `false` to stage for publishing.
- **Staged vs Live**: `listItems()` returns all items; `listItemsLive()` returns only published.

## Resources

- [Webflow API Quick Start](https://developers.webflow.com/data/reference/rest-introduction/quick-start)
- [CMS API Reference](https://developers.webflow.com/data/reference/cms)
- [SDK npm package](https://www.npmjs.com/package/webflow-api)

## Next Steps

Proceed to `webflow-local-dev-loop` for development workflow setup.
