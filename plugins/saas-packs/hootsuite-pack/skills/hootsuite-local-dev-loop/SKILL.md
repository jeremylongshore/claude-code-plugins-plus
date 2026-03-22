---
name: hootsuite-local-dev-loop
description: |
  Configure Hootsuite local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Hootsuite.
  Trigger with phrases like "hootsuite dev setup", "hootsuite local development",
  "hootsuite dev environment", "develop with hootsuite".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Local Dev Loop

## Overview

Set up a development workflow for Hootsuite API integrations with mocked API responses, token management, and testing.

## Instructions

### Step 1: Project Structure

```
hootsuite-integration/
├── src/
│   ├── hootsuite/
│   │   ├── client.ts       # API client with token refresh
│   │   ├── auth.ts         # OAuth 2.0 flow
│   │   ├── publishing.ts   # Message scheduling
│   │   └── analytics.ts    # Metrics retrieval
│   └── index.ts
├── tests/
│   ├── fixtures/           # Mock API responses
│   │   ├── profiles.json
│   │   └── messages.json
│   └── publishing.test.ts
├── .env.local
└── package.json
```

### Step 2: API Client with Auto Token Refresh

```typescript
// src/hootsuite/client.ts
import 'dotenv/config';

class HootsuiteClient {
  private accessToken: string;
  private refreshToken: string;
  private expiresAt: number;
  private base = 'https://platform.hootsuite.com/v1';

  constructor() {
    this.accessToken = process.env.HOOTSUITE_ACCESS_TOKEN!;
    this.refreshToken = process.env.HOOTSUITE_REFRESH_TOKEN!;
    this.expiresAt = Date.now() + 3600000;
  }

  async request(path: string, options: RequestInit = {}) {
    if (Date.now() > this.expiresAt - 60000) await this.refresh();
    const response = await fetch(`${this.base}${path}`, {
      ...options,
      headers: { 'Authorization': `Bearer ${this.accessToken}`, 'Content-Type': 'application/json', ...options.headers },
    });
    if (!response.ok) throw new Error(`Hootsuite API ${response.status}: ${await response.text()}`);
    return response.json();
  }

  private async refresh() {
    const res = await fetch('https://platform.hootsuite.com/oauth2/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': `Basic ${Buffer.from(`${process.env.HOOTSUITE_CLIENT_ID}:${process.env.HOOTSUITE_CLIENT_SECRET}`).toString('base64')}` },
      body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: this.refreshToken }),
    });
    const tokens = await res.json();
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    this.expiresAt = Date.now() + tokens.expires_in * 1000;
  }
}

export const hootsuite = new HootsuiteClient();
```

### Step 3: Mocked Tests

```typescript
// tests/publishing.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('Hootsuite Publishing', () => {
  beforeEach(() => vi.clearAllMocks());

  it('should schedule a message', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: [{ id: 'msg_123', state: 'SCHEDULED' }] }),
    });
    // Test scheduling logic
  });

  it('should list social profiles', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: [{ id: 'prof_1', type: 'TWITTER', socialNetworkUsername: 'test' }] }),
    });
    // Test profile listing
  });
});
```

## Output

- API client with automatic token refresh
- Mocked test suite
- Project structure for Hootsuite integrations

## Resources

- [Hootsuite REST API](https://developer.hootsuite.com/docs/using-rest-apis)
- [Vitest](https://vitest.dev/)

## Next Steps

See `hootsuite-sdk-patterns` for production patterns.
