---
name: canva-reference-architecture
description: |
  Implement Canva Connect API reference architecture with best-practice project layout.
  Use when designing new Canva integrations, reviewing project structure,
  or establishing architecture standards for Canva applications.
  Trigger with phrases like "canva architecture", "canva project structure",
  "how to organize canva", "canva layout", "canva reference".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Reference Architecture

## Overview

Production-ready architecture for Canva Connect API integrations. All interactions use the REST API at `api.canva.com/rest/v1/*` with OAuth 2.0 PKCE authentication.

## Project Structure

```
my-canva-integration/
├── src/
│   ├── canva/
│   │   ├── client.ts           # REST client wrapper with auto-refresh
│   │   ├── auth.ts             # OAuth 2.0 PKCE flow
│   │   ├── types.ts            # API request/response TypeScript types
│   │   └── errors.ts           # CanvaAPIError class
│   ├── services/
│   │   ├── design.service.ts   # Design creation, export, listing
│   │   ├── asset.service.ts    # Asset upload and management
│   │   ├── template.service.ts # Brand template autofill (Enterprise)
│   │   └── folder.service.ts   # Folder management
│   ├── routes/
│   │   ├── auth.ts             # OAuth callback endpoints
│   │   ├── designs.ts          # Design CRUD routes
│   │   ├── exports.ts          # Export trigger/download routes
│   │   └── webhooks.ts         # Webhook receiver
│   ├── middleware/
│   │   ├── auth.ts             # Verify user has valid Canva token
│   │   └── rate-limit.ts       # Client-side rate limit guard
│   ├── store/
│   │   └── tokens.ts           # Encrypted token storage (DB)
│   └── index.ts
├── tests/
│   ├── mocks/
│   │   └── canva-server.ts     # MSW mock server
│   ├── unit/
│   │   └── design.service.test.ts
│   └── integration/
│       └── canva-api.test.ts
├── .env.example
└── package.json
```

## Layer Architecture

```
┌─────────────────────────────────────────┐
│             Routes Layer                │
│   (Express/Next.js — HTTP in/out)       │
├─────────────────────────────────────────┤
│           Service Layer                 │
│  (Business logic, caching, validation)  │
├─────────────────────────────────────────┤
│          Canva Client Layer             │
│   (REST calls, token refresh, retry)    │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │
│    (Token store, cache, queue)          │
└─────────────────────────────────────────┘
```

## Service Layer Pattern

```typescript
// src/services/design.service.ts
import { CanvaClient } from '../canva/client';
import { LRUCache } from 'lru-cache';

export class DesignService {
  private cache = new LRUCache<string, any>({ max: 200, ttl: 300_000 });

  constructor(private canva: CanvaClient) {}

  async create(opts: {
    type: 'preset' | 'custom';
    name?: string;
    width?: number;
    height?: number;
    title: string;
    assetId?: string;
  }) {
    const designType = opts.type === 'preset'
      ? { type: 'preset' as const, name: opts.name! }
      : { type: 'custom' as const, width: opts.width!, height: opts.height! };

    return this.canva.request('/designs', {
      method: 'POST',
      body: JSON.stringify({
        design_type: designType,
        title: opts.title,
        ...(opts.assetId && { asset_id: opts.assetId }),
      }),
    });
  }

  async get(id: string) {
    const cached = this.cache.get(id);
    if (cached) return cached;

    const result = await this.canva.request(`/designs/${id}`);
    this.cache.set(id, result);
    return result;
  }

  async export(designId: string, format: object): Promise<string[]> {
    // Start export job
    const { job } = await this.canva.request('/exports', {
      method: 'POST',
      body: JSON.stringify({ design_id: designId, format }),
    });

    // Poll for completion
    return this.pollExport(job.id);
  }

  private async pollExport(exportId: string, timeoutMs = 60000): Promise<string[]> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const { job } = await this.canva.request(`/exports/${exportId}`);
      if (job.status === 'success') return job.urls;
      if (job.status === 'failed') throw new Error(`Export failed: ${job.error?.message}`);
      await new Promise(r => setTimeout(r, 2000));
    }
    throw new Error('Export timeout');
  }
}
```

## Data Flow

```
User clicks "Create Design"
       │
       ▼
┌─────────────┐
│   Route     │  POST /api/designs
│   Handler   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Design     │  Validates input, checks auth
│  Service    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Canva      │  POST api.canva.com/rest/v1/designs
│  Client     │  (auto-refreshes token if expired)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Canva      │  Returns design.id, edit_url, view_url
│  API        │
└─────────────┘
       │
       ▼
  Redirect user to edit_url → Canva Editor
```

## Auth Middleware

```typescript
// src/middleware/auth.ts
export function requireCanvaAuth(tokenStore: TokenStore) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;
    if (!userId) return res.status(401).json({ error: 'Not authenticated' });

    const tokens = await tokenStore.get(userId);
    if (!tokens) return res.status(403).json({ error: 'Canva not connected' });

    // Attach client to request for downstream use
    req.canva = new CanvaClient({
      clientId: process.env.CANVA_CLIENT_ID!,
      clientSecret: process.env.CANVA_CLIENT_SECRET!,
      tokens,
      onTokenRefresh: (newTokens) => tokenStore.save(userId, newTokens),
    });

    next();
  };
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Services import client, not vice versa |
| Token not found | User hasn't connected Canva | Redirect to OAuth flow |
| Cache stale | Design updated in Canva | Invalidate on webhook events |
| Service timeout | Export taking too long | Increase timeout, add job queue |

## Resources

- [Canva Starter Kit](https://github.com/canva-sdks/canva-connect-api-starter-kit)
- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)

## Next Steps

For multi-environment setup, see `canva-multi-env-setup`.
