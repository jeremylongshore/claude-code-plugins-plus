---
name: lucidchart-sdk-patterns
description: |
  Sdk Patterns for Lucidchart.
  Trigger: "lucidchart sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart SDK Patterns

## Overview
Lucid's REST API uses OAuth 2.0 with versioned `Lucid-Api-Version` headers to manage documents, pages, shapes, data-linked fields, and collaborative comments. A structured SDK client is essential because the API requires version negotiation on every request, returns deeply nested shape tree hierarchies, and enforces document-level locking for concurrent edits. These patterns provide OAuth token lifecycle management, typed shape and document models, fluent query building for filtered shape searches, and mock factories for diagramming test scenarios.

## Prerequisites
- Node.js 18+, TypeScript 5+
- `LUCID_CLIENT_ID` and `LUCID_CLIENT_SECRET` environment variables (OAuth 2.0 app credentials)
- `LUCID_ACCESS_TOKEN` or refresh token flow for per-user access
- `axios` or `node-fetch` for HTTP transport

## Singleton Client
```typescript
interface LucidConfig {
  clientId: string;
  clientSecret: string;
  accessToken: string;
  apiVersion?: string;
  baseUrl?: string;
}

let client: LucidClient | null = null;

export function getLucidClient(overrides?: Partial<LucidConfig>): LucidClient {
  if (!client) {
    const config: LucidConfig = {
      clientId: process.env.LUCID_CLIENT_ID ?? '',
      clientSecret: process.env.LUCID_CLIENT_SECRET ?? '',
      accessToken: process.env.LUCID_ACCESS_TOKEN ?? '',
      apiVersion: '2',
      baseUrl: 'https://api.lucid.co',
      ...overrides,
    };
    if (!config.accessToken) throw new Error('LUCID_ACCESS_TOKEN is required');
    client = new LucidClient(config);
  }
  return client;
}
```

## Error Wrapper
```typescript
interface LucidApiError { status: number; errorCode: string; message: string; documentId?: string; }

async function safeLucid<T>(fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    const parsed: LucidApiError = {
      status: err.response?.status ?? 500,
      errorCode: err.response?.data?.errorCode ?? 'INTERNAL',
      message: err.response?.data?.message ?? err.message,
      documentId: err.response?.data?.documentId,
    };
    if (parsed.status === 429) {
      const wait = parseInt(err.response?.headers?.['x-ratelimit-reset'] ?? '10', 10);
      await new Promise(r => setTimeout(r, wait * 1000));
      return fn();
    }
    if (parsed.errorCode === 'DOCUMENT_LOCKED') throw new Error(`Document ${parsed.documentId} is locked by another editor`);
    if (parsed.status === 403) throw new Error(`Insufficient permissions: ${parsed.message}`);
    throw new Error(`Lucid ${parsed.errorCode} (${parsed.status}): ${parsed.message}`);
  }
}
```

## Request Builder
```typescript
class ShapeQueryBuilder {
  private params: Record<string, string> = {};
  inDocument(docId: string) { this.params.documentId = docId; return this; }
  onPage(pageId: string) { this.params.pageId = pageId; return this; }
  ofType(shapeType: string) { this.params.className = shapeType; return this; }
  withDataField(key: string, value: string) { this.params[`data.${key}`] = value; return this; }
  limit(n: number) { this.params.limit = String(Math.min(n, 200)); return this; }
  offset(n: number) { this.params.offset = String(n); return this; }
  build(): URLSearchParams { return new URLSearchParams(this.params); }
}
```

## Response Types
```typescript
interface LucidDocument { id: string; title: string; editUrl: string; pageCount: number; lastModified: string; owner: string; }
interface LucidPage { id: string; title: string; index: number; width: number; height: number; }
interface LucidShape { id: string; className: string; boundingBox: { x: number; y: number; w: number; h: number }; text: string; dataFields: Record<string, string>; }
interface LucidComment { id: string; author: string; body: string; shapeId?: string; resolved: boolean; createdAt: string; }
```

## Middleware Pattern
```typescript
type Middleware = (req: RequestInit, next: () => Promise<Response>) => Promise<Response>;

const versionMiddleware: Middleware = (req, next) => {
  req.headers = { ...req.headers as Record<string, string>, 'Lucid-Api-Version': '2' };
  return next();
};
const oauthRefreshMiddleware = (refreshToken: string): Middleware => async (req, next) => {
  const res = await next();
  if (res.status === 401) {
    const tokens = await refreshOAuthToken(refreshToken);
    (req.headers as Record<string, string>).Authorization = `Bearer ${tokens.access_token}`;
    return next();
  }
  return res;
};
```

## Testing Utilities
```typescript
function mockDocument(overrides?: Partial<LucidDocument>): LucidDocument {
  return { id: 'doc_abc123', title: 'Architecture Diagram', editUrl: 'https://lucid.app/documents/edit/doc_abc123', pageCount: 3, lastModified: '2025-06-01T12:00:00Z', owner: 'user@example.com', ...overrides };
}
function mockShape(overrides?: Partial<LucidShape>): LucidShape {
  return { id: 'shape_001', className: 'ProcessBlock', boundingBox: { x: 100, y: 50, w: 200, h: 100 }, text: 'API Gateway', dataFields: {}, ...overrides };
}
function mockComment(shapeId: string): LucidComment {
  return { id: 'cmt_xyz', author: 'reviewer@example.com', body: 'Needs error path', shapeId, resolved: false, createdAt: '2025-06-02T09:00:00Z' };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| Version negotiation | API returns 400 on outdated version header | Catch version mismatch, retry with server-suggested version |
| Document lock retry | 409 DOCUMENT_LOCKED during shape updates | Exponential backoff up to 3 retries, then surface to user |
| OAuth token refresh | 401 on any endpoint | Use refresh token middleware, update stored access token |
| Permission escalation | 403 on shared document operations | Check document sharing settings before write operations |
| Shape tree validation | Creating shapes with invalid parent references | Validate page and container IDs exist before shape POST |

## Resources
- [Lucid API Reference](https://developer.lucid.co/reference/overview)

## Next Steps
Apply in `lucidchart-core-workflow-a`.
