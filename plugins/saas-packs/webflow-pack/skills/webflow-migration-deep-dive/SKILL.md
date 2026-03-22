---
name: webflow-migration-deep-dive
description: |
  Execute major Webflow migrations — from other CMS platforms to Webflow CMS,
  between Webflow sites, or large-scale content re-architecture using the Data API v2
  bulk endpoints, strangler fig pattern, and data validation.
  Trigger with phrases like "migrate to webflow", "webflow migration",
  "import into webflow", "webflow replatform", "move content to webflow",
  "webflow bulk import", "wordpress to webflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Migration Deep Dive

## Overview

Comprehensive guide for migrating content to Webflow CMS via the Data API v2.
Covers assessment, data mapping, bulk import (100 items/batch), validation,
and rollback. Handles WordPress, Contentful, Strapi, CSV, and JSON source formats.

## Prerequisites

- `webflow-api` SDK installed
- API token with `cms:read` and `cms:write` scopes
- Target Webflow site with CMS collections created in the Designer
- Source data exported (JSON, CSV, or API access)

## Migration Types

| Migration | Source | Complexity | Duration |
|-----------|--------|-----------|----------|
| CSV/JSON import | Static files | Low | Hours |
| WordPress | WP REST API | Medium | Days |
| Contentful/Strapi | Headless CMS API | Medium | Days |
| Site-to-site | Another Webflow site | Low | Hours |
| Full replatform | Custom CMS | High | Weeks |

## Instructions

### Step 1: Assess Target Collection Schema

Before importing, understand exactly what fields the target collection expects:

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

async function assessTarget(siteId: string) {
  const { collections } = await webflow.collections.list(siteId);

  const schema: Record<string, any> = {};

  for (const col of collections!) {
    schema[col.slug!] = {
      id: col.id,
      displayName: col.displayName,
      itemCount: col.itemCount,
      fields: col.fields?.map(f => ({
        slug: f.slug,
        displayName: f.displayName,
        type: f.type,
        required: f.isRequired,
        // Types: PlainText, RichText, Image, MultiImage, Video,
        //        Link, Email, Phone, Number, DateTime, Switch,
        //        Color, Option, File, Reference, MultiReference
      })),
    };
  }

  console.log(JSON.stringify(schema, null, 2));
  return schema;
}
```

### Step 2: Build Data Transformer

Map source data format to Webflow's `fieldData` structure:

```typescript
interface SourcePost {
  title: string;
  content: string;      // HTML content
  excerpt: string;
  author: string;
  date: string;          // ISO 8601
  categories: string[];
  featured_image?: string;
  status: "published" | "draft";
}

interface WebflowFieldData {
  name: string;          // Required system field
  slug: string;          // Required system field
  [key: string]: any;    // Custom fields use slug format
}

function transformPost(source: SourcePost): {
  fieldData: WebflowFieldData;
  isDraft: boolean;
} {
  return {
    isDraft: source.status === "draft",
    fieldData: {
      // System fields (always required)
      name: source.title,
      slug: slugify(source.title),
      // Custom fields (must match collection schema slugs)
      "post-body": source.content,
      "excerpt": source.excerpt,
      "author-name": source.author,
      "publish-date": source.date,
      // Image fields use Webflow asset URLs
      // You must upload images to Webflow first, or use external URLs
      ...(source.featured_image && {
        "hero-image": {
          url: source.featured_image,
          alt: source.title,
        },
      }),
    },
  };
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .substring(0, 256); // Webflow slug max length
}
```

### Step 3: WordPress Migration

```typescript
// Export from WordPress REST API
async function fetchWordPressPosts(wpUrl: string): Promise<SourcePost[]> {
  const posts: SourcePost[] = [];
  let page = 1;

  while (true) {
    const res = await fetch(`${wpUrl}/wp-json/wp/v2/posts?per_page=100&page=${page}`);
    if (!res.ok) break;

    const wpPosts = await res.json();
    if (wpPosts.length === 0) break;

    for (const wp of wpPosts) {
      posts.push({
        title: wp.title.rendered,
        content: wp.content.rendered,
        excerpt: wp.excerpt.rendered,
        author: wp.author_name || "Unknown",
        date: wp.date,
        categories: wp.categories || [],
        featured_image: wp.featured_media_url || undefined,
        status: wp.status === "publish" ? "published" : "draft",
      });
    }

    page++;
  }

  return posts;
}
```

### Step 4: CSV Import

```typescript
import { parse } from "csv-parse/sync";
import { readFileSync } from "fs";

function importFromCSV(filePath: string): SourcePost[] {
  const content = readFileSync(filePath, "utf-8");
  const records = parse(content, {
    columns: true,
    skip_empty_lines: true,
  });

  return records.map((row: any) => ({
    title: row.title || row.Title || row.name,
    content: row.content || row.body || row.description || "",
    excerpt: row.excerpt || row.summary || "",
    author: row.author || "Imported",
    date: row.date || row.published_at || new Date().toISOString(),
    categories: (row.categories || row.tags || "").split(",").map((s: string) => s.trim()),
    featured_image: row.image || row.featured_image || undefined,
    status: "published" as const,
  }));
}
```

### Step 5: Bulk Import Engine

```typescript
interface MigrationResult {
  total: number;
  created: number;
  skipped: number;
  failed: number;
  errors: Array<{ slug: string; error: string }>;
  duration: number;
}

async function bulkImport(
  collectionId: string,
  sourceItems: SourcePost[],
  options = { batchSize: 100, delayMs: 1000, dryRun: false }
): Promise<MigrationResult> {
  const start = Date.now();
  const result: MigrationResult = {
    total: sourceItems.length,
    created: 0,
    skipped: 0,
    failed: 0,
    errors: [],
    duration: 0,
  };

  // Get existing items to avoid duplicates
  const existing = await fetchAllExistingItems(collectionId);
  const existingSlugs = new Set(existing.map(i => i.fieldData?.slug));

  // Transform and filter
  const newItems = sourceItems
    .map(transformPost)
    .filter(item => {
      if (existingSlugs.has(item.fieldData.slug)) {
        result.skipped++;
        return false;
      }
      return true;
    });

  console.log(`Migration plan: ${newItems.length} new, ${result.skipped} skipped (duplicates)`);

  if (options.dryRun) {
    console.log("DRY RUN — no items will be created");
    result.duration = Date.now() - start;
    return result;
  }

  // Batch import
  for (let i = 0; i < newItems.length; i += options.batchSize) {
    const batch = newItems.slice(i, i + options.batchSize);
    const batchNum = Math.floor(i / options.batchSize) + 1;
    const totalBatches = Math.ceil(newItems.length / options.batchSize);

    try {
      await webflow.collections.items.createItemsBulk(collectionId, {
        items: batch,
      });
      result.created += batch.length;
      console.log(`Batch ${batchNum}/${totalBatches}: ${batch.length} items created`);
    } catch (error: any) {
      result.failed += batch.length;
      result.errors.push({
        slug: `batch-${batchNum}`,
        error: error.message,
      });
      console.error(`Batch ${batchNum} failed:`, error.message);
    }

    // Delay between batches to respect rate limits
    if (i + options.batchSize < newItems.length) {
      await new Promise(r => setTimeout(r, options.delayMs));
    }
  }

  result.duration = Date.now() - start;
  return result;
}

async function fetchAllExistingItems(collectionId: string) {
  const allItems = [];
  let offset = 0;

  while (true) {
    const { items, pagination } = await webflow.collections.items.listItems(
      collectionId,
      { offset, limit: 100 }
    );
    allItems.push(...(items || []));
    if (allItems.length >= (pagination?.total || 0)) break;
    offset += 100;
  }

  return allItems;
}
```

### Step 6: Post-Migration Validation

```typescript
async function validateMigration(
  collectionId: string,
  sourceCount: number
): Promise<{ valid: boolean; checks: Array<{ name: string; passed: boolean; detail: string }> }> {
  const checks = [];

  // 1. Item count check
  const { items, pagination } = await webflow.collections.items.listItems(
    collectionId, { limit: 1 }
  );
  const webflowCount = pagination?.total || 0;
  checks.push({
    name: "Item count",
    passed: webflowCount >= sourceCount,
    detail: `Webflow: ${webflowCount}, Source: ${sourceCount}`,
  });

  // 2. Required fields check (sample first 10 items)
  const { items: sample } = await webflow.collections.items.listItems(
    collectionId, { limit: 10 }
  );
  const missingFields = (sample || []).filter(
    i => !i.fieldData?.name || !i.fieldData?.slug
  );
  checks.push({
    name: "Required fields",
    passed: missingFields.length === 0,
    detail: `${missingFields.length} items missing name/slug`,
  });

  // 3. No duplicate slugs
  const allItems = await fetchAllExistingItems(collectionId);
  const slugs = allItems.map(i => i.fieldData?.slug);
  const uniqueSlugs = new Set(slugs);
  checks.push({
    name: "Unique slugs",
    passed: slugs.length === uniqueSlugs.size,
    detail: `${slugs.length - uniqueSlugs.size} duplicate slugs`,
  });

  // 4. Draft status check
  const draftCount = allItems.filter(i => i.isDraft).length;
  checks.push({
    name: "Published items",
    passed: true,
    detail: `${allItems.length - draftCount} published, ${draftCount} drafts`,
  });

  const valid = checks.every(c => c.passed);
  return { valid, checks };
}
```

### Step 7: Publish Migrated Content

```typescript
async function publishMigratedContent(collectionId: string) {
  const allItems = await fetchAllExistingItems(collectionId);
  const unpublished = allItems.filter(i => !i.isDraft).map(i => i.id!);

  // Publish in batches (publish endpoint accepts multiple IDs)
  for (let i = 0; i < unpublished.length; i += 100) {
    const batch = unpublished.slice(i, i + 100);
    await webflow.collections.items.publishItem(collectionId, {
      itemIds: batch,
    });
    console.log(`Published ${Math.min(i + 100, unpublished.length)}/${unpublished.length}`);

    if (i + 100 < unpublished.length) {
      await new Promise(r => setTimeout(r, 1000));
    }
  }
}
```

### Step 8: Rollback Plan

```typescript
async function rollbackMigration(collectionId: string, createdAfter: Date) {
  const allItems = await fetchAllExistingItems(collectionId);

  const migratedItems = allItems.filter(
    i => new Date(i.createdOn!) >= createdAfter
  );

  console.log(`Rolling back ${migratedItems.length} migrated items`);

  // Delete in batches of 100
  for (let i = 0; i < migratedItems.length; i += 100) {
    const batch = migratedItems.slice(i, i + 100).map(item => item.id!);
    await webflow.collections.items.deleteItemsBulk(collectionId, {
      itemIds: batch,
    });
    console.log(`Deleted batch ${Math.floor(i / 100) + 1}`);
    await new Promise(r => setTimeout(r, 500));
  }
}
```

## Complete Migration Script

```bash
# 1. Dry run first
npx tsx migrate.ts --source wordpress --wp-url https://myblog.com --dry-run

# 2. Execute migration
npx tsx migrate.ts --source wordpress --wp-url https://myblog.com

# 3. Validate
npx tsx migrate.ts --validate --collection-id col-xxx

# 4. Publish
npx tsx migrate.ts --publish --collection-id col-xxx

# 5. If something goes wrong:
npx tsx migrate.ts --rollback --collection-id col-xxx --after 2026-03-22
```

## Output

- Source data assessment and schema mapping
- Data transformer (WordPress, CSV, JSON, headless CMS)
- Bulk import engine (100 items/batch with rate limit handling)
- Post-migration validation (count, fields, duplicates)
- Content publishing automation
- Rollback procedure with time-based filtering

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad Request` | Field name mismatch | Compare transformer output to collection schema |
| `409 Conflict` | Duplicate slugs | Add suffix or use `createOrUpdate` pattern |
| `429 Rate Limited` | Too fast between batches | Increase `delayMs` |
| Missing images | External image URLs blocked | Upload to Webflow assets first |
| Truncated HTML | Content too long | Check Webflow field length limits |

## Resources

- [CMS API Reference](https://developers.webflow.com/data/reference/cms)
- [Bulk CMS Endpoints](https://developers.webflow.com/data/changelog/10232024)
- [Managing Collections](https://developers.webflow.com/data/docs/working-with-the-cms/manage-collections-and-items)
- [Migrating to API v2](https://developers.webflow.com/data/docs/migrating-to-v2)

## Next Steps

This is the final skill in the Webflow pack. For foundational setup, start with
`webflow-install-auth`.
