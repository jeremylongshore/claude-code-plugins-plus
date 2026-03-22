---
name: algolia-hello-world
description: |
  Create a minimal working Algolia example — index records and search them.
  Use when starting a new Algolia integration, testing your setup,
  or learning the saveObjects/searchSingleIndex pattern.
  Trigger: "algolia hello world", "algolia example", "algolia quick start", "first algolia search".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Hello World

## Overview

Index records into Algolia and search them back — the two fundamental operations. Uses the `algoliasearch` v5 client where all methods live on the client directly (no `initIndex`).

## Prerequisites

- `algoliasearch` v5 installed (`npm install algoliasearch`)
- `ALGOLIA_APP_ID` and `ALGOLIA_ADMIN_KEY` environment variables set
- See `algolia-install-auth` for setup

## Instructions

### Step 1: Index Records with saveObjects

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(
  process.env.ALGOLIA_APP_ID!,
  process.env.ALGOLIA_ADMIN_KEY!
);

// saveObjects adds or replaces records. Each must have objectID
// (or Algolia auto-generates one).
const { taskID } = await client.saveObjects({
  indexName: 'movies',
  objects: [
    { objectID: '1', title: 'The Matrix', year: 1999, genre: 'sci-fi' },
    { objectID: '2', title: 'Inception', year: 2010, genre: 'sci-fi' },
    { objectID: '3', title: 'Pulp Fiction', year: 1994, genre: 'crime' },
  ],
});

// Wait for indexing to complete before searching
await client.waitForTask({ indexName: 'movies', taskID });
console.log('Indexing complete.');
```

### Step 2: Search with searchSingleIndex

```typescript
// Basic search — Algolia searches all searchableAttributes by default
const { hits } = await client.searchSingleIndex({
  indexName: 'movies',
  searchParams: { query: 'matrix' },
});

console.log(`Found ${hits.length} results:`);
hits.forEach(hit => {
  // _highlightResult shows which parts matched
  console.log(`  ${hit.title} (${hit.year})`);
});
```

### Step 3: Configure Index Settings

```typescript
// Settings define how Algolia ranks results
await client.setSettings({
  indexName: 'movies',
  indexSettings: {
    searchableAttributes: ['title', 'genre'],       // Fields to search
    attributesForFaceting: ['genre', 'year'],        // Filterable fields
    customRanking: ['desc(year)'],                   // Tie-breaker: newer first
    attributesToRetrieve: ['title', 'year', 'genre'],// Fields returned in hits
  },
});
```

## Output

```
Indexing complete.
Found 1 results:
  The Matrix (1999)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid Application-ID or API key` | Wrong credentials | Verify in dashboard > Settings > API Keys |
| `Record is too big` | Object > 10KB (free) or 100KB (paid) | Reduce record size or split into smaller records |
| `Index does not exist` (on search) | Index not created yet | `saveObjects` auto-creates the index |
| `taskID` never resolves | Indexing queue backlog | Check dashboard > Indices > Operations |

## Examples

### Multi-Index Search (federated)

```typescript
// Search multiple indices in one API call
const { results } = await client.search({
  requests: [
    { indexName: 'movies', query: 'inception' },
    { indexName: 'actors', query: 'inception' },
  ],
});

results.forEach(result => {
  if ('hits' in result) {
    console.log(`${result.index}: ${result.hits.length} hits`);
  }
});
```

### Browse All Records (no query, iterate everything)

```typescript
// browse returns up to 1000 records per call — use for data export
const { hits, cursor } = await client.browse({
  indexName: 'movies',
  browseParams: { hitsPerPage: 1000 },
});

console.log(`First page: ${hits.length} records`);
// Use cursor to fetch next pages
```

### Delete Records

```typescript
// Delete by objectID
await client.deleteObject({ indexName: 'movies', objectID: '3' });

// Delete by query match
await client.deleteBy({
  indexName: 'movies',
  deleteByParams: { filters: 'genre:crime' },
});
```

## Resources

- [saveObjects Reference](https://www.algolia.com/doc/libraries/javascript/v5/methods/search/save-object/)
- [searchSingleIndex Reference](https://www.algolia.com/doc/libraries/javascript/v5/methods/search/search-single-index/)
- [Index Settings](https://www.algolia.com/doc/api-reference/api-methods/set-settings/)
- [Algolia Quick Start](https://www.algolia.com/doc/guides/getting-started/quick-start/)

## Next Steps

Proceed to `algolia-local-dev-loop` for development workflow setup.
