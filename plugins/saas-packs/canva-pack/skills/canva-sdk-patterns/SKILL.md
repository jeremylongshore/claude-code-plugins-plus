---
name: canva-sdk-patterns
description: |
  Apply production-ready Canva Connect API client patterns for TypeScript and Python.
  Use when building a reusable API client, implementing token refresh,
  or establishing team coding standards for Canva integrations.
  Trigger with phrases like "canva client patterns", "canva best practices",
  "canva code patterns", "canva API wrapper", "canva TypeScript client".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva SDK Patterns

## Overview

Production-ready patterns for wrapping the Canva Connect REST API. There is no official SDK — all integrations use `fetch` against `api.canva.com/rest/v1/*` with OAuth Bearer tokens. These patterns add automatic token refresh, retry logic, type safety, and multi-tenant support.

## Prerequisites

- Completed `canva-install-auth` setup
- Understanding of OAuth 2.0 token lifecycle
- TypeScript 5+ project (or Python 3.10+)

## Pattern 1: Type-Safe Client with Auto Token Refresh

```typescript
// src/canva/client.ts
interface CanvaTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number; // Unix ms
}

interface CanvaClientConfig {
  clientId: string;
  clientSecret: string;
  tokens: CanvaTokens;
  onTokenRefresh?: (tokens: CanvaTokens) => Promise<void>; // Persist new tokens
}

export class CanvaClient {
  private static BASE = 'https://api.canva.com/rest/v1';
  private tokens: CanvaTokens;

  constructor(private config: CanvaClientConfig) {
    this.tokens = config.tokens;
  }

  async request<T = any>(path: string, init: RequestInit = {}): Promise<T> {
    // Auto-refresh if token expires within 5 minutes
    if (Date.now() > this.tokens.expiresAt - 300_000) {
      await this.refreshToken();
    }

    const res = await fetch(`${CanvaClient.BASE}${path}`, {
      ...init,
      headers: {
        'Authorization': `Bearer ${this.tokens.accessToken}`,
        'Content-Type': 'application/json',
        ...init.headers,
      },
    });

    if (res.status === 401) {
      await this.refreshToken();
      return this.request(path, init); // Retry once after refresh
    }

    if (!res.ok) {
      const body = await res.text();
      throw new CanvaAPIError(res.status, body, path);
    }

    return res.status === 204 ? (null as T) : res.json();
  }

  private async refreshToken(): Promise<void> {
    const basicAuth = Buffer.from(
      `${this.config.clientId}:${this.config.clientSecret}`
    ).toString('base64');

    const res = await fetch(`${CanvaClient.BASE}/oauth/token`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${basicAuth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: this.tokens.refreshToken,
      }),
    });

    if (!res.ok) throw new Error('Token refresh failed — user must re-authorize');

    const data = await res.json();
    this.tokens = {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,  // Single-use — always store the new one
      expiresAt: Date.now() + data.expires_in * 1000,
    };

    await this.config.onTokenRefresh?.(this.tokens);
  }

  // Convenience methods matching the REST API
  async getMe() { return this.request('/users/me'); }
  async getProfile() { return this.request('/users/me/profile'); }
  async createDesign(body: object) { return this.request('/designs', { method: 'POST', body: JSON.stringify(body) }); }
  async getDesign(id: string) { return this.request(`/designs/${id}`); }
  async listDesigns(params?: URLSearchParams) { return this.request(`/designs?${params || ''}`); }
  async createExport(body: object) { return this.request('/exports', { method: 'POST', body: JSON.stringify(body) }); }
  async getExport(id: string) { return this.request(`/exports/${id}`); }
  async createAutofill(body: object) { return this.request('/autofills', { method: 'POST', body: JSON.stringify(body) }); }
  async getAutofill(id: string) { return this.request(`/autofills/${id}`); }
}
```

## Pattern 2: Custom Error Class

```typescript
// src/canva/errors.ts
export class CanvaAPIError extends Error {
  public readonly retryable: boolean;

  constructor(
    public readonly status: number,
    public readonly body: string,
    public readonly path: string
  ) {
    super(`Canva API ${status} on ${path}: ${body}`);
    this.name = 'CanvaAPIError';
    this.retryable = status === 429 || status >= 500;
  }

  get isRateLimited(): boolean { return this.status === 429; }
  get isAuthError(): boolean { return this.status === 401 || this.status === 403; }
  get isNotFound(): boolean { return this.status === 404; }
}
```

## Pattern 3: Retry with Exponential Backoff

```typescript
// src/canva/retry.ts
export async function withRetry<T>(
  fn: () => Promise<T>,
  opts = { maxRetries: 3, baseDelayMs: 1000 }
): Promise<T> {
  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === opts.maxRetries) throw err;
      if (err instanceof CanvaAPIError && !err.retryable) throw err;

      const delay = opts.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Pattern 4: Multi-Tenant Factory

```typescript
// src/canva/factory.ts
const clients = new Map<string, CanvaClient>();

export function getCanvaClientForUser(userId: string, db: TokenStore): CanvaClient {
  if (!clients.has(userId)) {
    const tokens = db.getTokens(userId);
    clients.set(userId, new CanvaClient({
      clientId: process.env.CANVA_CLIENT_ID!,
      clientSecret: process.env.CANVA_CLIENT_SECRET!,
      tokens,
      onTokenRefresh: async (newTokens) => {
        await db.saveTokens(userId, newTokens);
      },
    }));
  }
  return clients.get(userId)!;
}
```

## Pattern 5: Python REST Client

```python
# canva/client.py
import httpx
import base64
import time

class CanvaClient:
    BASE = "https://api.canva.com/rest/v1"

    def __init__(self, client_id: str, client_secret: str, tokens: dict):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokens = tokens
        self._http = httpx.AsyncClient(base_url=self.BASE, timeout=30)

    async def request(self, method: str, path: str, **kwargs) -> dict:
        if time.time() > self.tokens["expires_at"] - 300:
            await self._refresh()

        resp = await self._http.request(
            method, path,
            headers={"Authorization": f"Bearer {self.tokens['access_token']}"},
            **kwargs,
        )

        if resp.status_code == 401:
            await self._refresh()
            return await self.request(method, path, **kwargs)

        resp.raise_for_status()
        return resp.json() if resp.content else {}

    async def _refresh(self):
        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        resp = await self._http.post(
            "/oauth/token",
            headers={"Authorization": f"Basic {creds}"},
            data={"grant_type": "refresh_token", "refresh_token": self.tokens["refresh_token"]},
        )
        resp.raise_for_status()
        data = resp.json()
        self.tokens = {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": time.time() + data["expires_in"],
        }
```

## Response Validation with Zod

```typescript
import { z } from 'zod';

const CanvaDesignSchema = z.object({
  design: z.object({
    id: z.string(),
    title: z.string(),
    owner: z.object({ user_id: z.string(), team_id: z.string() }),
    urls: z.object({ edit_url: z.string(), view_url: z.string() }),
    created_at: z.number(),
    updated_at: z.number(),
    page_count: z.number(),
  }),
});

const validated = CanvaDesignSchema.parse(await client.getDesign(id));
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Auto-refresh | All API calls | Transparent token lifecycle |
| Error class | Error handling | Typed, retryable flags |
| Retry wrapper | Transient failures | Exponential backoff + jitter |
| Multi-tenant | SaaS apps | Per-user token isolation |

## Resources

- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Authentication](https://www.canva.dev/docs/connect/authentication/)
- [OpenAPI Spec](https://www.canva.dev/sources/connect/api/latest/api.yml)

## Next Steps

Apply patterns in `canva-core-workflow-a` for real-world usage.
