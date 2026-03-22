---
name: webflow-core-workflow-a
description: |
  Execute the primary Webflow workflow — CMS content management: list collections,
  CRUD items, publish items, and manage content lifecycle via the Data API v2.
  Use when working with Webflow CMS collections and items, managing blog posts,
  team members, or any dynamic content.
  Trigger with phrases like "webflow CMS", "webflow collections", "webflow items",
  "create webflow content", "manage webflow CMS", "webflow content management".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Core Workflow A — CMS Content Management

## Overview

The primary money-path workflow for Webflow: managing CMS collections and items
through the Data API v2. Covers the full CRUD lifecycle — create, read, update,
delete, and publish CMS content programmatically.

## Prerequisites

- Completed `webflow-install-auth` setup
- API token with `cms:read` and `cms:write` scopes
- A Webflow site with at least one CMS collection

## API Endpoints Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List collections | GET | `/v2/sites/{site_id}/collections` |
| Get collection | GET | `/v2/collections/{collection_id}` |
| List items (staged) | GET | `/v2/collections/{collection_id}/items` |
| List items (live) | GET | `/v2/collections/{collection_id}/items/live` |
| Get item | GET | `/v2/collections/{collection_id}/items/{item_id}` |
| Create item | POST | `/v2/collections/{collection_id}/items` |
| Create items (bulk) | POST | `/v2/collections/{collection_id}/items/bulk` |
| Update item | PATCH | `/v2/collections/{collection_id}/items/{item_id}` |
| Update items (bulk) | PATCH | `/v2/collections/{collection_id}/items/bulk` |
| Delete item | DELETE | `/v2/collections/{collection_id}/items/{item_id}` |
| Delete items (bulk) | DELETE | `/v2/collections/{collection_id}/items/bulk` |
| Publish item | POST | `/v2/collections/{collection_id}/items/publish` |

## Instructions

### Step 1: List Collections and Inspect Schema

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

async function inspectCollections(siteId: string) {
  const { collections } = await webflow.collections.list(siteId);

  for (const col of collections!) {
    console.log(`\n=== ${col.displayName} (${col.slug}) ===`);
    console.log(`ID: ${col.id}`);
    console.log(`Items: ${col.itemCount}`);
    console.log(`Fields:`);
    for (const field of col.fields || []) {
      const req = field.isRequired ? " [REQUIRED]" : "";
      console.log(`  ${field.slug} (${field.type})${req}`);
      // Types: PlainText, RichText, Image, MultiImage, Video,
      //        Link, Email, Phone, Number, DateTime, Switch,
      //        Color, Option, File, Reference, MultiReference,
      //        MembershipPlan
    }
  }
}
```

### Step 2: Create CMS Items

Items are created as drafts by default (`isDraft: true`). Field names use slug format.

```typescript
async function createItem(collectionId: string) {
  const item = await webflow.collections.items.createItem(collectionId, {
    isDraft: false, // false = staged for publishing
    fieldData: {
      // "name" and "slug" are required system fields
      name: "My New Blog Post",
      slug: "my-new-blog-post",
      // Custom fields use slug versions of field names
      "post-body": "<h2>Hello World</h2><p>Content here.</p>",
      "author-name": "Jeremy Longshore",
      "publish-date": new Date().toISOString(),
      "featured": true,
      // Reference fields use the referenced item's ID
      "category": "ref-item-id-here",
      // Image fields use the Webflow asset URL
      "hero-image": {
        url: "https://uploads-ssl.webflow.com/...",
        alt: "Hero image description",
      },
    },
  });

  console.log(`Created: ${item.id} (draft: ${item.isDraft})`);
  return item;
}
```

### Step 3: Bulk Create (Up to 100 Items)

```typescript
async function bulkCreate(collectionId: string) {
  const items = Array.from({ length: 50 }, (_, i) => ({
    fieldData: {
      name: `Product ${i + 1}`,
      slug: `product-${i + 1}`,
      price: (i + 1) * 9.99,
      description: `Description for product ${i + 1}`,
    },
    isDraft: false,
  }));

  const result = await webflow.collections.items.createItemsBulk(
    collectionId,
    { items }
  );

  console.log(`Bulk created: ${result.items?.length} items`);
  return result;
}
```

### Step 4: Read Items (Staged and Live)

```typescript
async function readItems(collectionId: string) {
  // Staged items (drafts + published, working copy)
  const staged = await webflow.collections.items.listItems(collectionId, {
    limit: 100, // Max 100 per request
    offset: 0,
    // Optional filters:
    // sortBy: "fieldData.name",
    // sortOrder: "asc",
  });

  console.log(`Staged items: ${staged.pagination?.total}`);

  // Live items (published only, what visitors see)
  const live = await webflow.collections.items.listItemsLive(collectionId, {
    limit: 100,
  });

  console.log(`Live items: ${live.pagination?.total}`);

  // Get single item by ID
  const item = await webflow.collections.items.getItem(
    collectionId,
    staged.items![0].id!
  );

  console.log(`Item: ${item.fieldData?.name}`);
}
```

### Step 5: Update Items

```typescript
async function updateItem(collectionId: string, itemId: string) {
  // PATCH — only send fields you want to change
  const updated = await webflow.collections.items.updateItem(
    collectionId,
    itemId,
    {
      fieldData: {
        name: "Updated Title",
        "post-body": "<p>Updated content</p>",
      },
    }
  );

  console.log(`Updated: ${updated.id} at ${updated.lastUpdated}`);
}

// Bulk update (up to 100 items)
async function bulkUpdate(collectionId: string, updates: Array<{ id: string; fields: Record<string, any> }>) {
  const items = updates.map(u => ({
    id: u.id,
    fieldData: u.fields,
  }));

  await webflow.collections.items.updateItemsBulk(collectionId, { items });
}
```

### Step 6: Publish Items

Publishing makes staged changes visible on the live site.

```typescript
async function publishItems(collectionId: string, itemIds: string[]) {
  // Publish specific items (not the whole site)
  await webflow.collections.items.publishItem(collectionId, {
    itemIds,
  });

  console.log(`Published ${itemIds.length} items`);
}

// Or publish the entire site (requires sites:write scope)
async function publishSite(siteId: string) {
  // Rate limit: max 1 publish per minute
  await webflow.sites.publish(siteId, {
    publishToWebflowSubdomain: true,
    // customDomains: ["example.com"], // Specify domains to publish to
  });

  console.log("Site published");
}
```

### Step 7: Delete Items

```typescript
async function deleteItem(collectionId: string, itemId: string) {
  await webflow.collections.items.deleteItem(collectionId, itemId);
  console.log(`Deleted: ${itemId}`);
}

// Bulk delete (up to 100 items)
async function bulkDelete(collectionId: string, itemIds: string[]) {
  await webflow.collections.items.deleteItemsBulk(collectionId, {
    itemIds,
  });
  console.log(`Deleted ${itemIds.length} items`);
}
```

## Complete Content Sync Example

```typescript
async function syncContentFromExternalCMS(
  siteId: string,
  collectionSlug: string,
  externalPosts: Array<{ title: string; body: string; publishedAt: string }>
) {
  // 1. Find the target collection
  const { collections } = await webflow.collections.list(siteId);
  const collection = collections!.find(c => c.slug === collectionSlug);
  if (!collection) throw new Error(`Collection "${collectionSlug}" not found`);

  // 2. Get existing items to avoid duplicates
  const { items: existing } = await webflow.collections.items.listItems(collection.id!);
  const existingSlugs = new Set(existing!.map(i => i.fieldData?.slug));

  // 3. Create new items (skip duplicates)
  const newPosts = externalPosts.filter(
    p => !existingSlugs.has(slugify(p.title))
  );

  if (newPosts.length === 0) {
    console.log("No new posts to sync");
    return;
  }

  // 4. Bulk create (batches of 100)
  const items = newPosts.map(p => ({
    isDraft: false,
    fieldData: {
      name: p.title,
      slug: slugify(p.title),
      "post-body": p.body,
      "publish-date": p.publishedAt,
    },
  }));

  const created = await webflow.collections.items.createItemsBulk(
    collection.id!,
    { items: items.slice(0, 100) }
  );

  // 5. Publish the new items
  const newIds = created.items!.map(i => i.id!);
  await webflow.collections.items.publishItem(collection.id!, {
    itemIds: newIds,
  });

  console.log(`Synced and published ${newIds.length} new posts`);
}

function slugify(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}
```

## Output

- Full CMS CRUD operations (create, read, update, delete)
- Bulk operations up to 100 items per request
- Separate staged vs live item access
- Item publishing (individual items or full site)
- Content sync workflow from external sources

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad Request` | Invalid field data or missing required fields | Check collection schema for required fields |
| `404 Not Found` | Wrong collection_id or item_id | List collections first with `collections.list()` |
| `409 Conflict` | Duplicate slug in collection | Use unique slugs or add suffix |
| `429 Too Many Requests` | Rate limit exceeded | SDK auto-retries; for bulk, add delays between batches |
| Site publish 429 | >1 publish/minute | Wait 60s between site publishes |

## Resources

- [CMS API Reference](https://developers.webflow.com/data/reference/cms)
- [Managing Collections and Items](https://developers.webflow.com/data/docs/working-with-the-cms/manage-collections-and-items)
- [Bulk CMS Endpoints](https://developers.webflow.com/data/changelog/10232024)

## Next Steps

For site, page, and ecommerce management, see `webflow-core-workflow-b`.
