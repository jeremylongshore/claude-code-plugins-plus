---
name: glean-sdk-patterns
description: 'Apply production-ready Glean API patterns with typed clients, batch
  indexing, pagination, and error handling.

  Trigger: "glean SDK patterns", "glean best practices", "glean API client".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean SDK Patterns

## Overview
Production-ready patterns for the Glean enterprise search platform. Glean uses POST-based REST endpoints for both search and indexing. Search queries go to the Client API while document ingestion uses the Indexing API. A structured client centralizes token management, enforces batch pagination for bulk indexing, and provides typed responses for search results.

## Singleton Client
```typescript
let _client: GleanClient | null = null;
export function getClient(): GleanClient {
  if (!_client) {
    const domain = process.env.GLEAN_DOMAIN, key = process.env.GLEAN_API_KEY;
    if (!domain || !key) throw new Error('GLEAN_DOMAIN and GLEAN_API_KEY must be set');
    _client = new GleanClient(domain, key);
  }
  return _client;
}
class GleanClient {
  private base: string; private h: Record<string, string>;
  constructor(domain: string, key: string) {
    this.base = `https://${domain}/api`;
    this.h = { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' };
  }
  async search(query: string, opts: { pageSize?: number; datasource?: string } = {}) {
    const r = await fetch(`${this.base}/client/v1/search`, { method: 'POST',
      headers: { ...this.h, 'X-Glean-Auth-Type': 'BEARER' },
      body: JSON.stringify({ query, pageSize: opts.pageSize ?? 20,
        requestOptions: opts.datasource ? { datasourceFilter: opts.datasource } : undefined }) });
    if (!r.ok) throw new GleanError(r.status, await r.text()); return r.json() as Promise<GleanSearchResponse>;
  }
  async indexDocuments(datasource: string, docs: GleanDocument[]): Promise<void> {
    const r = await fetch(`${this.base}/index/v1/indexdocuments`, {
      method: 'POST', headers: this.h, body: JSON.stringify({ datasource, documents: docs }) });
    if (!r.ok) throw new GleanError(r.status, await r.text());
  }
  async bulkIndex(ds: string, docs: GleanDocument[], batch = 100): Promise<void> {
    for (let i = 0; i < docs.length; i += batch) await this.indexDocuments(ds, docs.slice(i, i + batch));
  }
}
```

## Error Wrapper
```typescript
export class GleanError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'GleanError'; }
}
export async function safeCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    if (err instanceof GleanError && err.status === 429) { await new Promise(r => setTimeout(r, 3000)); return fn(); }
    if (err instanceof GleanError && err.status === 401) throw new GleanError(401, 'Invalid GLEAN_API_KEY');
    throw new GleanError(err.status ?? 0, `${operation} failed: ${err.message}`);
  }
}
```

## Request Builder
```typescript
class GleanSearchBuilder {
  private body: Record<string, any> = {};
  query(q: string) { this.body.query = q; return this; }
  datasource(ds: string) { this.body.requestOptions = { datasourceFilter: ds }; return this; }
  pageSize(n: number) { this.body.pageSize = Math.min(n, 100); return this; }
  cursor(token: string) { this.body.cursor = token; return this; }
  facets(fields: string[]) { this.body.facetFilters = fields; return this; }
  build() { return this.body; }
}
// Usage: new GleanSearchBuilder().query('onboarding docs').datasource('confluence').pageSize(10).build();
```

## Response Types
```typescript
interface GleanDocument {
  id: string; title: string; url: string;
  body: { mimeType: string; textContent: string };
  author?: { email: string }; updatedAt?: string;
}
interface GleanSearchResponse {
  results: Array<{ document: GleanDocument; snippets: string[]; score: number }>;
  totalResults: number; cursor?: string;
}
interface GleanDatasource { name: string; displayName: string; documentCount: number; lastCrawledAt: string; }
```

## Testing Utilities
```typescript
export function mockDocument(o: Partial<GleanDocument> = {}): GleanDocument {
  return { id: 'doc-001', title: 'Onboarding Guide', url: 'https://wiki.example.com/onboarding',
    body: { mimeType: 'text/plain', textContent: 'Welcome to the team...' },
    author: { email: 'hr@example.com' }, updatedAt: '2025-03-01T00:00:00Z', ...o };
}
export function mockSearchResponse(n = 3): GleanSearchResponse {
  return { results: Array.from({ length: n }, (_, i) => ({
    document: mockDocument({ id: `doc-${i}` }), snippets: ['...match...'], score: 0.95 - i * 0.1 })), totalResults: n };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All search and index calls | Structured error with operation context |
| Retry on 429 | Bulk indexing pipelines | 3s delay before retry |
| Batch pagination | Indexing > 100 documents | `bulkIndex` with batch tracking |
| Auth validation | Client init | Fail fast on missing `GLEAN_API_KEY` |

## Resources
- [Glean Developer Portal](https://developers.glean.com/)

## Next Steps
Apply patterns in `glean-core-workflow-a`.
