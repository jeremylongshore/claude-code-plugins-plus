---
name: glean-core-workflow-b
description: |
  Execute Glean secondary workflow: bulk document indexing, custom datasource connectors,
  and content lifecycle management via the Indexing API.
  Trigger: "glean bulk index", "glean custom connector", "glean datasource", "glean indexing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Core Workflow B: Indexing & Connectors

## Overview

Build custom Glean connectors: set up datasources, bulk index documents, manage content lifecycle, and configure permissions.

## Instructions

### Step 1: Create Custom Datasource

```typescript
await fetch(`${GLEAN}/index/v1/adddatasource`, {
  method: 'POST', headers: idxHeaders,
  body: JSON.stringify({
    name: 'internal_docs',
    displayName: 'Internal Documentation',
    datasourceCategory: 'PUBLISHED_CONTENT',
    urlRegex: 'https://docs.internal.company.com/.*',
    isOnPrem: false,
  }),
});
```

### Step 2: Bulk Index Documents

```typescript
// Bulk indexing replaces ALL documents in the datasource
const uploadId = `upload-${Date.now()}`;

// Send documents in batches of 100
for (let i = 0; i < allDocs.length; i += 100) {
  const batch = allDocs.slice(i, i + 100);
  const isFirst = i === 0;
  const isLast = i + 100 >= allDocs.length;

  await fetch(`${GLEAN}/index/v1/bulkindexdocuments`, {
    method: 'POST', headers: idxHeaders,
    body: JSON.stringify({
      datasource: 'internal_docs',
      uploadId,
      isFirstPage: isFirst,
      isLastPage: isLast,
      documents: batch.map(doc => ({
        id: doc.id,
        title: doc.title,
        url: doc.url,
        body: { mimeType: 'text/html', textContent: doc.content },
        author: { email: doc.authorEmail },
        updatedAt: doc.updatedAt,
        permissions: { allowAnonymousAccess: true },
      })),
    }),
  });
  console.log(`Indexed batch ${i/100 + 1} (${batch.length} docs)`);
}
```

### Step 3: Set Document Permissions

```typescript
// Control who can see documents in search results
await fetch(`${GLEAN}/index/v1/indexdocuments`, {
  method: 'POST', headers: idxHeaders,
  body: JSON.stringify({
    datasource: 'internal_docs',
    documents: [{
      id: 'confidential-001',
      title: 'Board Meeting Notes',
      url: 'https://docs.internal.company.com/board/q1-2025',
      body: { mimeType: 'text/plain', textContent: '...' },
      permissions: {
        allowedUsers: [{ email: 'ceo@company.com' }, { email: 'cfo@company.com' }],
      },
    }],
  }),
});
```

### Step 4: Delete Documents

```typescript
// Remove specific documents from the index
await fetch(`${GLEAN}/index/v1/deletedocument`, {
  method: 'POST', headers: idxHeaders,
  body: JSON.stringify({
    datasource: 'internal_docs',
    objectType: 'Document',
    id: 'doc-to-delete',
  }),
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `uploadId already used` | Reusing bulk upload ID | Generate unique uploadId per run |
| `document too large` | Content exceeds limit | Truncate body to ~100KB |
| `invalid permissions` | Malformed user/group | Use valid email addresses |

## Resources

- [Bulk Indexing](https://developers.glean.com/api-info/indexing/documents/bulk-indexing)
- [Document Permissions](https://developers.glean.com/api-info/indexing/documents/permissions)
- [Custom Datasources](https://docs.glean.com/connectors/custom/about)

## Next Steps

For common errors, see `glean-common-errors`.
