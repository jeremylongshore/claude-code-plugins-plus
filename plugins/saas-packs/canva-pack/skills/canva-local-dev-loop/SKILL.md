---
name: canva-local-dev-loop
description: |
  Configure Canva Connect API local development with hot reload and mock server.
  Use when setting up a development environment, testing OAuth flows locally,
  or establishing a fast iteration cycle for Canva integrations.
  Trigger with phrases like "canva dev setup", "canva local development",
  "canva dev environment", "develop with canva", "canva mock".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Local Dev Loop

## Overview

Set up a fast local development environment for Canva Connect API integrations with a token management server, mock API for testing, and hot reload.

## Prerequisites

- Completed `canva-install-auth` setup
- Node.js 18+ with npm/pnpm
- ngrok or similar tunnel for OAuth callbacks (or use localhost with Canva dev settings)

## Instructions

### Step 1: Project Structure

```
my-canva-app/
├── src/
│   ├── canva/
│   │   ├── client.ts       # REST client wrapper (from canva-sdk-patterns)
│   │   ├── auth.ts          # OAuth PKCE flow
│   │   └── types.ts         # API response types
│   ├── routes/
│   │   ├── auth.ts          # OAuth callback handler
│   │   └── designs.ts       # Design CRUD routes
│   └── index.ts
├── tests/
│   ├── canva-mock.ts        # Mock Canva API server
│   └── designs.test.ts
├── .env.local               # Local secrets (git-ignored)
├── .env.example             # Template for team
├── package.json
└── tsconfig.json
```

### Step 2: Environment Setup

```bash
# .env.example
CANVA_CLIENT_ID=
CANVA_CLIENT_SECRET=
CANVA_REDIRECT_URI=http://localhost:3000/auth/canva/callback
PORT=3000

# Copy and fill in
cp .env.example .env.local
```

### Step 3: OAuth Callback Server

```typescript
// src/routes/auth.ts
import express from 'express';
import { generatePKCE, getAuthorizationUrl, exchangeCodeForToken } from '../canva/auth';

const router = express.Router();
const pkceStore = new Map<string, string>(); // state → verifier

router.get('/auth/canva/start', (req, res) => {
  const { verifier, challenge } = generatePKCE();
  const state = crypto.randomUUID();
  pkceStore.set(state, verifier);

  const url = getAuthorizationUrl({
    clientId: process.env.CANVA_CLIENT_ID!,
    redirectUri: process.env.CANVA_REDIRECT_URI!,
    scopes: ['design:content:write', 'design:content:read', 'design:meta:read', 'asset:write'],
    codeChallenge: challenge,
    state,
  });

  res.redirect(url);
});

router.get('/auth/canva/callback', async (req, res) => {
  const { code, state } = req.query as { code: string; state: string };
  const verifier = pkceStore.get(state);
  if (!verifier) return res.status(400).send('Invalid state');
  pkceStore.delete(state);

  const tokens = await exchangeCodeForToken({
    code,
    codeVerifier: verifier,
    clientId: process.env.CANVA_CLIENT_ID!,
    clientSecret: process.env.CANVA_CLIENT_SECRET!,
    redirectUri: process.env.CANVA_REDIRECT_URI!,
  });

  // Store tokens securely (database in production, file for dev)
  console.log('Access token received, expires in', tokens.expires_in, 'seconds');
  res.send('Authenticated! You can close this tab.');
});
```

### Step 4: Hot Reload Config

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "tunnel": "ngrok http 3000"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "vitest": "^2.0.0",
    "@types/express": "^4.17.0"
  }
}
```

### Step 5: Mock Canva API for Testing

```typescript
// tests/canva-mock.ts
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const mockDesign = {
  design: {
    id: 'DAVZr1z5464',
    title: 'Test Design',
    owner: { user_id: 'UAFd3s5464', team_id: 'TAFd3s5464' },
    urls: {
      edit_url: 'https://www.canva.com/design/DAVZr1z5464/edit',
      view_url: 'https://www.canva.com/design/DAVZr1z5464/view',
    },
    created_at: 1700000000,
    updated_at: 1700000000,
    page_count: 1,
  },
};

export const canvaMock = setupServer(
  http.get('https://api.canva.com/rest/v1/users/me', () =>
    HttpResponse.json({ team_user: { user_id: 'UAFd3s5464', team_id: 'TAFd3s5464' } })
  ),

  http.post('https://api.canva.com/rest/v1/designs', () =>
    HttpResponse.json(mockDesign)
  ),

  http.get('https://api.canva.com/rest/v1/designs/:id', () =>
    HttpResponse.json(mockDesign)
  ),

  http.post('https://api.canva.com/rest/v1/exports', () =>
    HttpResponse.json({
      job: { id: 'EXP123', status: 'success', urls: ['https://export.canva.com/file.pdf'] },
    })
  ),
);
```

### Step 6: Integration Tests with Mocks

```typescript
// tests/designs.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { canvaMock } from './canva-mock';
import { CanvaClient } from '../src/canva/client';

beforeAll(() => canvaMock.listen());
afterAll(() => canvaMock.close());

describe('Canva Designs', () => {
  const client = new CanvaClient({
    clientId: 'test', clientSecret: 'test',
    tokens: { accessToken: 'test-token', refreshToken: 'test', expiresAt: Date.now() + 3600000 },
  });

  it('should get user identity', async () => {
    const me = await client.getMe();
    expect(me.team_user.user_id).toBeDefined();
  });

  it('should create a design', async () => {
    const result = await client.createDesign({
      design_type: { type: 'custom', width: 1080, height: 1080 },
      title: 'Test Design',
    });
    expect(result.design.id).toBe('DAVZr1z5464');
  });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| OAuth callback fails | Redirect URI mismatch | Match URI exactly in Canva dashboard |
| `ERR_SSL_PROTOCOL` from ngrok | Using HTTP callback | Use ngrok HTTPS URL |
| Token not persisting | In-memory only | Save to `.canva-tokens.json` in dev |
| Mock not intercepting | Wrong URL pattern | Verify full URL including `/rest/v1` prefix |

## Resources

- [Canva Connect Quickstart](https://www.canva.dev/docs/connect/quickstart/)
- [Canva Starter Kit](https://github.com/canva-sdks/canva-connect-api-starter-kit)
- [MSW Documentation](https://mswjs.io/)

## Next Steps

See `canva-sdk-patterns` for production-ready code patterns.
