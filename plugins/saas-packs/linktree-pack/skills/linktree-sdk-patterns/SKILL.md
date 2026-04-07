---
name: linktree-sdk-patterns
description: |
  Sdk Patterns for Linktree.
  Trigger: "linktree sdk patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree SDK Patterns

## Overview
Linktree's REST API exposes profile management, link CRUD, click analytics, and appearance theming through bearer-token authentication. A structured SDK client matters here because Linktree enforces strict per-minute rate limits on analytics endpoints and returns nested profile objects that benefit from strong typing. These patterns provide a thread-safe singleton, typed error classification, fluent request building for paginated link lists, and test utilities for mocking profile and analytics responses.

## Prerequisites
- Node.js 18+, TypeScript 5+
- `LINKTREE_API_KEY` environment variable (generated in Linktree admin > Settings > Developer)
- `axios` or `node-fetch` for HTTP transport

## Singleton Client
```typescript
interface LinktreeConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

let client: LinktreeClient | null = null;

export function getLinktreeClient(overrides?: Partial<LinktreeConfig>): LinktreeClient {
  if (!client) {
    const config: LinktreeConfig = {
      apiKey: process.env.LINKTREE_API_KEY ?? '',
      baseUrl: 'https://api.linktr.ee/v1',
      timeout: 10_000,
      ...overrides,
    };
    if (!config.apiKey) throw new Error('LINKTREE_API_KEY is required');
    client = new LinktreeClient(config);
  }
  return client;
}
```

## Error Wrapper
```typescript
interface LinktreeError { status: number; code: string; detail: string; }

async function safeLinktree<T>(fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    const parsed: LinktreeError = {
      status: err.response?.status ?? 500,
      code: err.response?.data?.error?.code ?? 'UNKNOWN',
      detail: err.response?.data?.error?.message ?? err.message,
    };
    if (parsed.status === 429) {
      const retryAfter = parseInt(err.response?.headers?.['retry-after'] ?? '5', 10);
      await new Promise(r => setTimeout(r, retryAfter * 1000));
      return fn();
    }
    if (parsed.status === 401) throw new Error(`Auth failed: ${parsed.detail}`);
    throw new Error(`Linktree ${parsed.code} (${parsed.status}): ${parsed.detail}`);
  }
}
```

## Request Builder
```typescript
class LinkQueryBuilder {
  private params: Record<string, string> = {};
  forProfile(id: string) { this.params.profile_id = id; return this; }
  active(only = true) { this.params.is_active = String(only); return this; }
  page(cursor: string) { this.params.cursor = cursor; return this; }
  limit(n: number) { this.params.limit = String(Math.min(n, 100)); return this; }
  build(): URLSearchParams { return new URLSearchParams(this.params); }
}
```

## Response Types
```typescript
interface LinktreeProfile { id: string; username: string; tier: 'free' | 'pro' | 'premium'; created_at: string; }
interface LinktreeLink { id: string; title: string; url: string; position: number; is_active: boolean; thumbnail_url?: string; }
interface LinkAnalytics { link_id: string; clicks: number; unique_visitors: number; period: string; }
interface PaginatedLinks { data: LinktreeLink[]; cursor?: string; has_more: boolean; }
```

## Middleware Pattern
```typescript
type Middleware = (req: RequestInit, next: () => Promise<Response>) => Promise<Response>;

const authMiddleware: Middleware = (req, next) => {
  req.headers = { ...req.headers as Record<string, string>, Authorization: `Bearer ${process.env.LINKTREE_API_KEY}` };
  return next();
};
const loggingMiddleware: Middleware = async (req, next) => {
  const start = Date.now();
  const res = await next();
  console.log(`[linktree] ${req.method} ${res.status} ${Date.now() - start}ms`);
  return res;
};
```

## Testing Utilities
```typescript
function mockProfile(overrides?: Partial<LinktreeProfile>): LinktreeProfile {
  return { id: 'prof_test_123', username: 'testuser', tier: 'pro', created_at: '2025-01-01T00:00:00Z', ...overrides };
}
function mockLink(overrides?: Partial<LinktreeLink>): LinktreeLink {
  return { id: 'link_abc', title: 'My Site', url: 'https://example.com', position: 0, is_active: true, ...overrides };
}
function mockAnalytics(linkId: string): LinkAnalytics {
  return { link_id: linkId, clicks: 142, unique_visitors: 98, period: '7d' };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| Retry with backoff | 429 rate limit on analytics endpoints | Parse `Retry-After` header, wait, retry once |
| Auth refresh | 401 on any endpoint | Re-fetch API key from vault, rebuild client singleton |
| Graceful degrade | Analytics endpoint down | Return cached click counts, log warning |
| Validation guard | Creating links with invalid URLs | Check URL format before API call, throw typed error |
| Idempotency check | Duplicate link creation | Query existing links by URL before POST |

## Resources
- [Linktree API Reference](https://linktr.ee/marketplace/developer)

## Next Steps
Apply in `linktree-core-workflow-a`.
