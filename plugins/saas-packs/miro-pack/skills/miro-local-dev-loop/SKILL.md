---
name: miro-local-dev-loop
description: |
  Configure Miro local development with hot reload, testing, and ngrok tunneling.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with the Miro REST API v2.
  Trigger with phrases like "miro dev setup", "miro local development",
  "miro dev environment", "develop with miro", "miro testing".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, development, testing]
compatible-with: claude-code
---

# Miro Local Dev Loop

## Overview

Set up a fast local development workflow for building Miro integrations, including hot reload, test mocking against the REST API v2, and ngrok tunneling for webhooks.

## Prerequisites

- Completed `miro-install-auth` setup
- Node.js 18+ with npm or pnpm
- Access token with `boards:read` and `boards:write` scopes
- ngrok (for webhook development)

## Instructions

### Step 1: Project Structure

```
my-miro-app/
├── src/
│   ├── miro/
│   │   ├── client.ts       # MiroApi wrapper singleton
│   │   ├── boards.ts       # Board CRUD operations
│   │   ├── items.ts        # Item operations (sticky notes, shapes, etc.)
│   │   └── types.ts        # Response type definitions
│   ├── webhooks/
│   │   └── handler.ts      # Webhook event processing
│   └── index.ts
├── tests/
│   ├── miro-client.test.ts
│   └── fixtures/
│       ├── board.json       # Sample board response
│       └── sticky-note.json # Sample item response
├── .env.local               # Local secrets (git-ignored)
├── .env.example             # Template for team
├── package.json
└── tsconfig.json
```

### Step 2: Package Configuration

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "MIRO_TEST_MODE=live vitest run tests/integration/",
    "tunnel": "ngrok http 3000",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@mirohq/miro-api": "^2.0.0",
    "express": "^4.18.0",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^1.0.0",
    "typescript": "^5.0.0"
  }
}
```

### Step 3: Miro Client Singleton

```typescript
// src/miro/client.ts
import { MiroApi } from '@mirohq/miro-api';

let instance: MiroApi | null = null;

export function getMiroApi(): MiroApi {
  if (!instance) {
    const token = process.env.MIRO_ACCESS_TOKEN;
    if (!token) throw new Error('MIRO_ACCESS_TOKEN not set');
    instance = new MiroApi(token);
  }
  return instance;
}

// For testing — allow injecting a mock
export function resetMiroApi(): void {
  instance = null;
}
```

### Step 4: Test Fixtures from Real API Responses

```json
// tests/fixtures/board.json
{
  "id": "uXjVN1234567890",
  "type": "board",
  "name": "Test Board",
  "description": "Fixture for unit tests",
  "createdAt": "2025-01-15T10:00:00Z",
  "modifiedAt": "2025-01-15T10:30:00Z",
  "owner": { "id": "123456", "type": "user", "name": "Dev User" },
  "policy": {
    "sharingPolicy": { "access": "private" },
    "permissionsPolicy": { "collaborationToolsStartAccess": "all_editors" }
  }
}
```

```json
// tests/fixtures/sticky-note.json
{
  "id": "3458764500000001",
  "type": "sticky_note",
  "data": { "content": "Test note", "shape": "square" },
  "style": { "fillColor": "light_yellow", "textAlign": "center" },
  "position": { "x": 100, "y": 200, "origin": "center" },
  "geometry": { "width": 199 },
  "createdAt": "2025-01-15T10:05:00Z",
  "modifiedAt": "2025-01-15T10:05:00Z",
  "createdBy": { "id": "123456", "type": "user" }
}
```

### Step 5: Unit Tests with Vitest Mocks

```typescript
// tests/miro-client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import boardFixture from './fixtures/board.json';
import stickyNoteFixture from './fixtures/sticky-note.json';

// Mock fetch for Miro API calls
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('Miro Board Operations', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('should create a sticky note on a board', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => stickyNoteFixture,
    });

    const response = await fetch(
      'https://api.miro.com/v2/boards/uXjVN123/sticky_notes',
      {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test-token',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: { content: 'Test note', shape: 'square' },
          position: { x: 100, y: 200 },
        }),
      }
    );

    const note = await response.json();
    expect(note.type).toBe('sticky_note');
    expect(note.data.content).toBe('Test note');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/v2/boards/'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('should handle 429 rate limit responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      headers: new Headers({
        'X-RateLimit-Remaining': '0',
        'Retry-After': '5',
      }),
      json: async () => ({ status: 429, message: 'Rate limit exceeded' }),
    });

    const response = await fetch('https://api.miro.com/v2/boards', {
      headers: { 'Authorization': 'Bearer test-token' },
    });

    expect(response.status).toBe(429);
  });
});
```

### Step 6: Ngrok Tunneling for Webhooks

```bash
# Start your dev server
npm run dev

# In another terminal, start ngrok
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.app)
# Register it as a webhook callback in your Miro app settings
# or via the API (see miro-webhooks-events skill)
```

### Step 7: Debug Logging

```typescript
// Enable verbose HTTP logging during development
import { MiroApi } from '@mirohq/miro-api';

// Log all API requests and responses
const api = new MiroApi(process.env.MIRO_ACCESS_TOKEN!, {
  logger: {
    info: (...args) => console.log('[MIRO]', ...args),
    warn: (...args) => console.warn('[MIRO]', ...args),
    error: (...args) => console.error('[MIRO]', ...args),
  },
});
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MIRO_ACCESS_TOKEN` | Yes | OAuth 2.0 access token |
| `MIRO_CLIENT_ID` | For OAuth flow | App client ID |
| `MIRO_CLIENT_SECRET` | For OAuth flow | App client secret |
| `MIRO_REDIRECT_URI` | For OAuth flow | OAuth callback URL |
| `MIRO_TEST_BOARD_ID` | For integration tests | Board ID for live tests |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `MIRO_ACCESS_TOKEN not set` | Missing env variable | Copy `.env.example` to `.env.local` |
| `ECONNREFUSED` on webhook test | Dev server not running | Start with `npm run dev` first |
| `invalid_token` | Expired access token | Refresh token (see `miro-install-auth`) |
| Mock not matching | Fixture out of date | Re-capture fixture from live API |

## Resources

- [Miro Node.js Quickstart](https://developers.miro.com/docs/miro-nodejs-quickstart)
- [Vitest Documentation](https://vitest.dev/)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps

See `miro-sdk-patterns` for production-ready code patterns.
