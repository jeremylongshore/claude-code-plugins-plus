---
name: glean-sdk-patterns
description: |
  Apply production-ready Glean API patterns with typed clients, batch indexing, pagination, and error handling.
  Trigger: "glean SDK patterns", "glean best practices", "glean API client".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean SDK Patterns

## Typed Glean Client

```typescript
class GleanClient {
  private indexUrl: string;
  private searchUrl: string;

  constructor(private domain: string, private indexToken: string, private clientToken: string) {
    this.indexUrl = `https://${domain}/api/index/v1`;
    this.searchUrl = `https://${domain}/api/client/v1`;
  }

  async indexDocuments(datasource: string, docs: GleanDocument[]) {
    const res = await fetch(`${this.indexUrl}/indexdocuments`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.indexToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ datasource, documents: docs }),
    });
    if (!res.ok) throw new Error(`Glean index error ${res.status}: ${await res.text()}`);
    return res.json();
  }

  async search(query: string, options: { pageSize?: number; datasource?: string } = {}) {
    const res = await fetch(`${this.searchUrl}/search`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.clientToken}`,
        'X-Glean-Auth-Type': 'BEARER',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        pageSize: options.pageSize ?? 20,
        requestOptions: options.datasource ? { datasourceFilter: options.datasource } : undefined,
      }),
    });
    if (!res.ok) throw new Error(`Glean search error ${res.status}: ${await res.text()}`);
    return res.json();
  }

  async bulkIndex(datasource: string, docs: GleanDocument[], batchSize = 100) {
    const uploadId = `bulk-${Date.now()}`;
    for (let i = 0; i < docs.length; i += batchSize) {
      const batch = docs.slice(i, i + batchSize);
      await fetch(`${this.indexUrl}/bulkindexdocuments`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.indexToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          datasource, uploadId,
          isFirstPage: i === 0,
          isLastPage: i + batchSize >= docs.length,
          documents: batch,
        }),
      });
    }
  }
}

interface GleanDocument {
  id: string;
  title: string;
  url: string;
  body: { mimeType: string; textContent: string };
  author?: { email: string };
  updatedAt?: string;
  permissions?: { allowAnonymousAccess?: boolean; allowedUsers?: Array<{ email: string }> };
}
```

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Index Documents API](https://developers.glean.com/api/indexing-api/index-documents)
