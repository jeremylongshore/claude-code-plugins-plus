---
name: glean-hello-world
description: |
  Index documents into Glean and search them back using the Indexing and Client APIs.
  Use when starting a new Glean custom connector, testing search quality,
  or learning the index/search pattern.
  Trigger: "glean hello world", "glean example", "glean index document", "glean search".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Hello World

## Overview

Index documents into Glean and search them. Two steps: set up a custom datasource with the Indexing API, then query with the Client API.

## Instructions

### Step 1: Set Up Custom Datasource

```typescript
const GLEAN = `https://${process.env.GLEAN_DOMAIN}/api`;
const idxHeaders = {
  'Authorization': `Bearer ${process.env.GLEAN_INDEXING_TOKEN}`,
  'Content-Type': 'application/json',
};

// Create or configure a custom datasource
await fetch(`${GLEAN}/index/v1/adddatasource`, {
  method: 'POST', headers: idxHeaders,
  body: JSON.stringify({
    name: 'my_wiki',
    displayName: 'Internal Wiki',
    datasourceCategory: 'PUBLISHED_CONTENT',
    urlRegex: 'https://wiki.company.com/.*',
    iconUrl: 'https://wiki.company.com/favicon.ico',
  }),
});
```

### Step 2: Index Documents

```typescript
// Index individual documents
await fetch(`${GLEAN}/index/v1/indexdocuments`, {
  method: 'POST', headers: idxHeaders,
  body: JSON.stringify({
    datasource: 'my_wiki',
    documents: [{
      id: 'doc-001',
      title: 'Getting Started Guide',
      url: 'https://wiki.company.com/getting-started',
      body: { mimeType: 'text/plain', textContent: 'This guide covers onboarding steps...' },
      author: { email: 'jane@company.com' },
      updatedAt: new Date().toISOString(),
      permissions: { allowAnonymousAccess: true },
    }],
  }),
});
console.log('Document indexed.');
```

### Step 3: Search

```typescript
const searchHeaders = {
  'Authorization': `Bearer ${process.env.GLEAN_CLIENT_TOKEN}`,
  'X-Glean-Auth-Type': 'BEARER',
  'Content-Type': 'application/json',
};

const results = await fetch(`${GLEAN}/client/v1/search`, {
  method: 'POST', headers: searchHeaders,
  body: JSON.stringify({
    query: 'onboarding getting started',
    pageSize: 10,
    requestOptions: { datasourceFilter: 'my_wiki' },
  }),
}).then(r => r.json());

results.results?.forEach((r: any) => {
  console.log(`${r.title} (${r.url}) — score: ${r.score}`);
});
```

## Output

```
Document indexed.
Getting Started Guide (https://wiki.company.com/getting-started) — score: 0.95
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `datasource not found` | Datasource not created | Run `adddatasource` first |
| No search results | Indexing not yet complete | Wait 1-2 minutes for processing |
| `invalid document` | Missing required fields | Include `id`, `title`, `url` |

## Resources

- [Indexing API Overview](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/search)
- [Index Documents](https://developers.glean.com/api/indexing-api/index-documents)

## Next Steps

Proceed to `glean-local-dev-loop` for development workflow setup.
