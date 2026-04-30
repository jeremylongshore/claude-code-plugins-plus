---
name: onenote-core-workflow-b
description: 'Search, query, and paginate OneNote content with OData filters and client-side
  search patterns.

  Use when building search features, querying pages across notebooks, or handling
  large result sets.

  Trigger with "onenote search", "onenote query pages", "onenote pagination", "find
  onenote content".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote — Search, Query, and Pagination

## Overview

OneNote's dedicated search endpoint was deprecated in April 2024. The replacement — OData `$filter` queries on page listings — cannot search page body content, cannot search across all notebooks in a single call, and sometimes returns deleted pages in results. Pagination via `@odata.nextLink` is unreliable: the link is sometimes omitted even when more results exist. This skill provides production-tested patterns for content discovery, cross-notebook queries, and safe pagination with guard rails.

Key pain points addressed:
- The `$search` parameter on `/me/onenote/pages` is deprecated — use `$filter` on metadata fields only
- No single endpoint searches across all notebooks — you must iterate notebooks and their sections
- Deleted pages continue appearing in `GET /sections/{id}/pages` results for up to 30 minutes
- `@odata.nextLink` may be absent even when `$top` items were returned (Graph bug with OneNote)

## Prerequisites

- Azure app registration with delegated permissions: `Notes.Read` or `Notes.ReadWrite`
- App-only auth deprecated March 31, 2025 — use delegated auth only
- Python: `pip install msgraph-sdk azure-identity`
- Node/TypeScript: `npm install @microsoft/microsoft-graph-client @azure/identity @azure/msal-node`
- Optional for client-side search: `npm install fuse.js` or `pip install thefuzz`

## Instructions

### Step 1 — Query Pages with OData Filters

OData `$filter` works on page metadata fields — not body content. Supported fields: `title`, `createdDateTime`, `lastModifiedDateTime`.

```typescript
import { Client } from "@microsoft/microsoft-graph-client";

// Filter by title substring
const results = await client.api("/me/onenote/pages")
  .filter("contains(title, 'sprint planning')")
  .select("id,title,lastModifiedDateTime,parentSection")
  .top(20)
  .orderby("lastModifiedDateTime desc")
  .get();

// Filter by date range
const recentPages = await client.api("/me/onenote/pages")
  .filter("lastModifiedDateTime ge 2026-03-01T00:00:00Z")
  .select("id,title,lastModifiedDateTime")
  .top(50)
  .orderby("lastModifiedDateTime desc")
  .get();
```

> **Warning:** `$search` was deprecated April 2024. Using it returns `400 Bad Request` on most tenants. Use `$filter` with `contains()` on title, or implement client-side search on fetched content.

### Step 2 — Cross-Notebook Search Pattern

There is no single Graph endpoint that searches page content across all notebooks. You must iterate:

```typescript
interface SearchResult {
  pageId: string;
  title: string;
  sectionName: string;
  notebookName: string;
  lastModified: string;
  snippet?: string;
}

async function searchAcrossNotebooks(
  client: Client,
  query: string
): Promise<SearchResult[]> {
  const results: SearchResult[] = [];
  const notebooks = await client.api("/me/onenote/notebooks")
    .select("id,displayName")
    .get();

  for (const notebook of notebooks.value) {
    const sections = await client.api(
      `/me/onenote/notebooks/${notebook.id}/sections`
    ).select("id,displayName").get();

    for (const section of sections.value) {
      const pages = await client.api(
        `/me/onenote/sections/${section.id}/pages`
      )
        .filter(`contains(title, '${query.replace(/'/g, "''")}')`)
        .select("id,title,lastModifiedDateTime")
        .top(50)
        .get();

      for (const page of pages.value ?? []) {
        results.push({
          pageId: page.id,
          title: page.title,
          sectionName: section.displayName,
          notebookName: notebook.displayName,
          lastModified: page.lastModifiedDateTime,
        });
      }
    }
  }
  return results;
}
```

> **Performance:** This approach makes N+M API calls (N notebooks + M total sections). For users with many notebooks, cache the notebook/section structure and only fetch pages from recently modified sections.

### Step 3 — Client-Side Full-Text Search

Since `$filter` only works on metadata, search page body content client-side after fetching:

```typescript
import Fuse from "fuse.js";

interface IndexedPage {
  id: string;
  title: string;
  plainText: string;
  sectionId: string;
}

// Build the index (do this once, cache it)
async function buildSearchIndex(client: Client, sectionId: string): Promise<Fuse<IndexedPage>> {
  const pages = await client.api(`/me/onenote/sections/${sectionId}/pages`)
    .select("id,title")
    .top(100)
    .get();

  const indexed: IndexedPage[] = [];
  for (const page of pages.value) {
    const contentStream = await client.api(
      `/me/onenote/pages/${page.id}/content`
    ).get();
    // Strip HTML tags for plain text search
    const html = await streamToString(contentStream);
    const plainText = html.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
    indexed.push({ id: page.id, title: page.title, plainText, sectionId });
  }

  return new Fuse(indexed, {
    keys: [
      { name: "title", weight: 2 },
      { name: "plainText", weight: 1 },
    ],
    threshold: 0.3,
    includeScore: true,
  });
}

// Search
const fuse = await buildSearchIndex(client, sectionId);
const results = fuse.search("deployment checklist");
```

### Step 4 — Safe Pagination with Guard Rails

The `@odata.nextLink` from OneNote endpoints is sometimes missing even when more results exist. Always implement a safety limit:

```typescript
interface PaginatedResult<T> {
  items: T[];
  totalFetched: number;
  hitSafetyLimit: boolean;
}

async function paginateAll<T>(
  client: Client,
  initialUrl: string,
  maxPages: number = 20,  // Safety limit: prevent runaway pagination
  pageSize: number = 100
): Promise<PaginatedResult<T>> {
  const items: T[] = [];
  let url: string | null = `${initialUrl}${initialUrl.includes("?") ? "&" : "?"}$top=${pageSize}`;
  let pagesConsumed = 0;

  while (url && pagesConsumed < maxPages) {
    const response = await client.api(url).get();
    const batch = response.value ?? [];
    items.push(...batch);
    pagesConsumed++;

    // Guard: if we got fewer items than $top, we're at the end
    // even if @odata.nextLink is present (Graph bug)
    if (batch.length < pageSize) break;

    url = response["@odata.nextLink"] ?? null;

    // Guard: if no nextLink but we got exactly $top items,
    // the API may have dropped the link — try manual offset
    if (!url && batch.length === pageSize) {
      console.warn("Missing @odata.nextLink — attempting manual $skip");
      const skip = items.length;
      url = `${initialUrl}${initialUrl.includes("?") ? "&" : "?"}$top=${pageSize}&$skip=${skip}`;
    }
  }

  return {
    items,
    totalFetched: items.length,
    hitSafetyLimit: pagesConsumed >= maxPages,
  };
}
```

### Step 5 — Filter Deleted Pages from Results

Deleted pages can appear in list results for up to 30 minutes. Filter them before displaying:

```typescript
async function getActivePages(client: Client, sectionId: string) {
  const result = await paginateAll(
    client,
    `/me/onenote/sections/${sectionId}/pages?$select=id,title,lastModifiedDateTime,createdDateTime&$orderby=lastModifiedDateTime desc`
  );

  // Deleted pages have null title and a lastModifiedDateTime
  // very close to their deletion time
  const activePages = result.items.filter((page: any) => {
    if (!page.title) return false;  // Deleted pages often have null titles
    return true;
  });

  // Additional verification: try to GET content for suspicious pages
  // A 404 on content means the page is deleted
  return activePages;
}
```

### Step 6 — Python Async Pagination

```python
from msgraph import GraphServiceClient

async def paginate_pages(client: GraphServiceClient, section_id: str, max_pages: int = 20):
    """Paginate through all pages in a section with safety limits."""
    all_pages = []
    pages_fetched = 0

    result = await client.me.onenote.sections.by_onenote_section_id(
        section_id
    ).pages.get()

    while result and pages_fetched < max_pages:
        all_pages.extend(result.value or [])
        pages_fetched += 1

        if not result.odata_next_link:
            break

        # Follow @odata.nextLink
        result = await client.me.onenote.sections.by_onenote_section_id(
            section_id
        ).pages.with_url(result.odata_next_link).get()

    return all_pages
```

## Output

Search and query operations return:
- **Page listing:** JSON array with `id`, `title`, `createdDateTime`, `lastModifiedDateTime`, `parentSection`
- **Page content:** XHTML stream (must be buffered and parsed)
- **Pagination:** `@odata.nextLink` URL (when present) or `@odata.count` (when `$count=true` is specified)

## Error Handling

| Status | Cause | Fix |
|--------|-------|-----|
| 400 | Deprecated `$search` parameter, malformed `$filter` syntax | Use `$filter` with `contains()` — not `$search` |
| 400 | Invalid OData operator (e.g., `eq` on title) | Only `contains()` and `startswith()` work on string fields |
| 404 | Page deleted but appeared in listing | Filter by non-null title; verify with `GET /pages/{id}` |
| 429 | Rate limited during cross-notebook iteration | Implement per-request delays; see `onenote-rate-limits` |
| 502 | Token expired mid-pagination | Refresh auth token and resume from last `@odata.nextLink` |

## Examples

**TypeScript — Search recent pages modified this week:**
```typescript
const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
const recent = await client.api("/me/onenote/pages")
  .filter(`lastModifiedDateTime ge ${oneWeekAgo}`)
  .select("id,title,lastModifiedDateTime")
  .orderby("lastModifiedDateTime desc")
  .top(50)
  .get();

console.log(`Found ${recent.value.length} pages modified in the last 7 days`);
```

**Python — Count pages per section:**
```python
notebooks = await client.me.onenote.notebooks.get()
for nb in notebooks.value:
    sections = await client.me.onenote.notebooks.by_notebook_id(
        nb.id
    ).sections.get()
    for sec in sections.value:
        pages = await client.me.onenote.sections.by_onenote_section_id(
            sec.id
        ).pages.get()
        count = len(pages.value) if pages.value else 0
        print(f"{nb.display_name}/{sec.display_name}: {count} pages")
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Get Content](https://learn.microsoft.com/en-us/graph/onenote-get-content)
- [Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)

## Next Steps

- See `onenote-core-workflow-a` for CRUD operations on notebooks, sections, and pages
- See `onenote-rate-limits` for throttling cross-notebook search patterns
- See `onenote-performance-tuning` for `$select` optimization and caching strategies
