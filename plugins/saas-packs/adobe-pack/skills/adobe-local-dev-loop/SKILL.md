---
name: adobe-local-dev-loop
description: |
  Configure Adobe local development with App Builder CLI, Runtime actions,
  hot reload, and mock testing for Firefly/PDF/Photoshop APIs.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Adobe APIs.
  Trigger with phrases like "adobe dev setup", "adobe local development",
  "adobe dev environment", "develop with adobe", "aio app".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Local Dev Loop

## Overview

Set up a fast local development workflow for Adobe integrations using the `aio` CLI for App Builder projects, or a standalone Node.js setup for direct API usage (Firefly Services, PDF Services).

## Prerequisites

- Completed `adobe-install-auth` setup
- Node.js 18+ with npm/pnpm
- Adobe Developer Console project configured
- `@adobe/aio-cli` installed globally (for App Builder projects)

## Instructions

### Step 1: Choose Your Project Type

**Option A — App Builder (serverless Runtime actions):**
```bash
# Install Adobe I/O CLI
npm install -g @adobe/aio-cli

# Login (opens browser for IMS auth)
aio login

# Create new App Builder project
aio app init my-adobe-app
# Select: Firefly Services, Adobe I/O Events, etc.

# Run locally with hot reload
aio app run
# Serves at https://localhost:9080 with live Runtime action emulation
```

**Option B — Standalone SDK project:**
```bash
mkdir my-adobe-project && cd my-adobe-project
npm init -y
npm install @adobe/pdfservices-node-sdk @adobe/firefly-apis dotenv
npm install -D typescript tsx vitest @types/node
```

### Step 2: Project Structure

```
my-adobe-project/
├── src/
│   ├── adobe/
│   │   ├── auth.ts           # OAuth token management (from install-auth)
│   │   ├── firefly.ts        # Firefly API client wrapper
│   │   ├── pdf-services.ts   # PDF Services client wrapper
│   │   └── photoshop.ts      # Photoshop API client wrapper
│   └── index.ts
├── tests/
│   ├── fixtures/
│   │   └── sample.pdf        # Test PDF for extraction tests
│   ├── adobe-auth.test.ts
│   └── firefly.test.ts
├── .env.local                # Local secrets (git-ignored)
├── .env.example              # Template for team
├── tsconfig.json
└── package.json
```

### Step 3: Configure Hot Reload and Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "vitest --config vitest.integration.config.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

### Step 4: Mock Adobe APIs for Unit Tests

```typescript
// tests/adobe-auth.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the global fetch for token endpoint
const mockFetch = vi.fn();
global.fetch = mockFetch;

import { getAdobeAccessToken } from '../src/adobe/auth';

describe('Adobe OAuth Auth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.ADOBE_CLIENT_ID = 'test-client-id';
    process.env.ADOBE_CLIENT_SECRET = 'test-secret';
    process.env.ADOBE_SCOPES = 'openid,AdobeID';
  });

  it('should fetch and cache access token', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'test-token-123',
        token_type: 'bearer',
        expires_in: 86400,
      }),
    });

    const token = await getAdobeAccessToken();
    expect(token).toBe('test-token-123');
    expect(mockFetch).toHaveBeenCalledWith(
      'https://ims-na1.adobelogin.com/ims/token/v3',
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('should throw on auth failure', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => 'invalid_client',
    });

    await expect(getAdobeAccessToken()).rejects.toThrow('Adobe auth failed');
  });
});
```

### Step 5: Integration Test with Real API

```typescript
// tests/firefly-integration.test.ts
import { describe, it, expect } from 'vitest';
import { getAdobeAccessToken } from '../src/adobe/auth';

describe.skipIf(!process.env.ADOBE_CLIENT_ID)('Firefly Integration', () => {
  it('should generate an image from prompt', async () => {
    const token = await getAdobeAccessToken();

    const response = await fetch(
      'https://firefly-api.adobe.io/v3/images/generate',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-api-key': process.env.ADOBE_CLIENT_ID!,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: 'A simple red circle on white background',
          n: 1,
          size: { width: 512, height: 512 },
        }),
      }
    );

    expect(response.ok).toBe(true);
    const result = await response.json();
    expect(result.outputs).toHaveLength(1);
    expect(result.outputs[0].image.url).toMatch(/^https:\/\//);
  }, 30_000); // 30s timeout for API call
});
```

## Output

- Working development environment with hot reload via `tsx watch`
- Unit test suite with mocked Adobe auth and API responses
- Integration test that validates real API connectivity
- `.env.example` template for team onboarding

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `aio login` hangs | Browser popup blocked | Use `aio login --no-open` and copy URL manually |
| `Module not found: @adobe/pdfservices-node-sdk` | Missing install | Run `npm install @adobe/pdfservices-node-sdk` |
| Test timeout on integration | Slow API or rate limit | Increase vitest timeout; check `Retry-After` header |
| `ADOBE_CLIENT_ID undefined` | Missing `.env.local` | Copy `.env.example` to `.env.local` and fill in values |

## Resources

- [Adobe App Builder First App](https://developer.adobe.com/app-builder/docs/get_started/app_builder_get_started/first-app)
- [Adobe I/O CLI Reference](https://developer.adobe.com/app-builder/docs/guides/runtime_guides/reference_docs/cli-use)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

See `adobe-sdk-patterns` for production-ready code patterns.
