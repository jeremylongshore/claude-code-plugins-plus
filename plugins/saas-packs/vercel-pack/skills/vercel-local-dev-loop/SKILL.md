---
name: vercel-local-dev-loop
description: |
  Configure Vercel local development with vercel dev, environment variables, and hot reload.
  Use when setting up a development environment, testing serverless functions locally,
  or establishing a fast iteration cycle with Vercel.
  Trigger with phrases like "vercel dev setup", "vercel local development",
  "vercel dev environment", "develop with vercel locally".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, development, testing, workflow]

---
# Vercel Local Dev Loop

## Overview
Run Vercel serverless functions and API routes locally using `vercel dev`. Covers environment variable management, hot reload, local testing patterns, and framework-specific dev servers.

## Prerequisites
- Completed `vercel-install-auth` setup
- Project linked via `vercel link`
- Node.js 18+ with npm/pnpm

## Instructions

### Step 1: Pull Environment Variables
```bash
# Pull env vars from Vercel to local .env files
vercel env pull .env.development.local

# This creates .env.development.local with all Development-scoped vars:
# VERCEL="1"
# VERCEL_ENV="development"
# DATABASE_URL="postgres://..."
# API_SECRET="sk-..."
```

### Step 2: Start Local Dev Server
```bash
# vercel dev starts a local server that emulates the Vercel platform
vercel dev

# Output:
# Vercel CLI 39.x.x — dev command
# > Ready on http://localhost:3000

# With a specific port
vercel dev --listen 8080

# With debug logging
vercel dev --debug
```

`vercel dev` provides:
- Serverless function emulation at `/api/*` routes
- Automatic TypeScript compilation
- `vercel.json` rewrites, redirects, and headers applied locally
- Environment variables loaded from `.env*.local` files
- Framework detection (Next.js, Nuxt, SvelteKit, etc.)

### Step 3: Test Serverless Functions Locally
```bash
# Test your API route
curl http://localhost:3000/api/hello
# {"message":"Hello from Vercel Serverless Function!"}

# Test with POST body
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"test@example.com"}'

# Test with query parameters
curl "http://localhost:3000/api/search?q=vercel&limit=10"
```

### Step 4: Framework-Specific Dev Servers
For frameworks with their own dev server, use those instead of `vercel dev`:

```bash
# Next.js — built-in Vercel compatibility
npx next dev
# API routes at pages/api/* or app/api/* work identically

# Nuxt
npx nuxi dev

# SvelteKit
npm run dev

# Astro
npx astro dev
```

The framework dev servers handle API routes natively. Use `vercel dev` only for plain serverless function projects without a framework.

### Step 5: Local Environment Variable Management
```bash
# Add a new env var for development only
vercel env add MY_VAR development
# Prompts for value, stores encrypted on Vercel

# List all env vars
vercel env ls

# Remove an env var
vercel env rm MY_VAR development

# Pull updated vars after changes
vercel env pull .env.development.local
```

### Step 6: Testing with Vitest
```typescript
// api/__tests__/hello.test.ts
import { describe, it, expect, vi } from 'vitest';

// Mock the Vercel request/response
function createMockReq(overrides = {}) {
  return { method: 'GET', query: {}, body: null, ...overrides };
}

function createMockRes() {
  const res: any = {};
  res.status = vi.fn().mockReturnValue(res);
  res.json = vi.fn().mockReturnValue(res);
  res.send = vi.fn().mockReturnValue(res);
  return res;
}

describe('GET /api/hello', () => {
  it('returns 200 with message', async () => {
    const handler = (await import('../hello')).default;
    const req = createMockReq();
    const res = createMockRes();

    handler(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({ message: expect.any(String) })
    );
  });
});
```

## `.env` File Hierarchy
Vercel loads environment files in this order (later files override earlier):

| File | Environment | Git |
|------|------------|-----|
| `.env` | All | Commit |
| `.env.local` | All (local only) | Ignore |
| `.env.development` | Development | Commit |
| `.env.development.local` | Development (local only) | Ignore |

## Output
- Local dev server running with serverless function emulation
- Environment variables synced from Vercel to local `.env` files
- Hot reload on file changes
- Test suite for serverless function handlers

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `vercel dev` hangs on start | Port already in use | Kill the process on port 3000 or use `--listen 8080` |
| `Error: No framework detected` | Missing package.json or framework | Add a build framework or use plain functions in `api/` |
| Env var undefined locally | Not pulled from Vercel | Run `vercel env pull .env.development.local` |
| `FUNCTION_INVOCATION_TIMEOUT` | Function exceeds 10s locally | Check for unresolved promises or infinite loops |
| TypeScript errors in `api/` | Missing `@vercel/node` types | `npm install --save-dev @vercel/node` |

## Resources
- [Vercel Dev Command](https://vercel.com/docs/cli/dev)
- [Environment Variables](https://vercel.com/docs/environment-variables)
- [Vercel Functions](https://vercel.com/docs/functions)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps
Proceed to `vercel-sdk-patterns` for production-ready REST API integration patterns.
