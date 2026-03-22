---
name: vercel-known-pitfalls
description: |
  Identify and avoid Vercel anti-patterns and common integration mistakes.
  Use when reviewing Vercel code for issues, onboarding new developers,
  or auditing existing Vercel deployments for best practice violations.
  Trigger with phrases like "vercel mistakes", "vercel anti-patterns",
  "vercel pitfalls", "vercel what not to do", "vercel code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, audit, anti-patterns, best-practices]

---
# Vercel Known Pitfalls

## Overview
Catalog of the most common Vercel anti-patterns with severity ratings, detection methods, and fixes. Organized by category: secret exposure, serverless function mistakes, edge runtime violations, configuration errors, and cost traps.

## Prerequisites
- Access to Vercel codebase for review
- Understanding of Vercel's deployment model
- Familiarity with `vercel-common-errors` for error codes

## Instructions

### Category 1: Secret Exposure (Critical)

**P1: Secrets in NEXT_PUBLIC_ variables**
```typescript
// BAD — exposed in client JavaScript bundle, visible to anyone
const apiKey = process.env.NEXT_PUBLIC_API_SECRET;
// This value is inlined at build time into the browser bundle

// GOOD — server-only access
const apiKey = process.env.API_SECRET;
// Only accessible in serverless functions and server components
```
- **Detection:** `grep -r 'NEXT_PUBLIC_.*SECRET\|NEXT_PUBLIC_.*KEY\|NEXT_PUBLIC_.*TOKEN' src/`
- **Fix:** Remove `NEXT_PUBLIC_` prefix, rotate the exposed secret immediately

**P2: Hardcoded credentials in source**
```typescript
// BAD
const client = new Client({ apiKey: 'sk_live_abc123' });

// GOOD
const client = new Client({ apiKey: process.env.API_KEY });
```
- **Detection:** `grep -rE 'sk_live|sk_test|Bearer [a-zA-Z0-9]{20,}' src/ api/`
- **Fix:** Move to environment variables, add pre-commit hook

**P3: Secrets in vercel.json**
```json
// BAD — vercel.json is committed to git
{
  "env": { "API_KEY": "sk_live_abc123" }
}

// GOOD — use Vercel dashboard or CLI
// vercel env add API_KEY production
```

### Category 2: Serverless Function Mistakes (High)

**P4: Heavy initialization at module level**
```typescript
// BAD — runs on every cold start, adds 500ms+
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient(); // Connects on import
const cache = await loadLargeDataset(); // Blocks cold start

// GOOD — lazy initialization
let prisma: PrismaClient | null = null;
function getDb() {
  if (!prisma) prisma = new PrismaClient();
  return prisma;
}

export default async function handler(req, res) {
  const db = getDb(); // Only connects on first request
  // ...
}
```

**P5: Not returning responses from all code paths**
```typescript
// BAD — some paths don't return, causing NO_RESPONSE_FROM_FUNCTION
export default function handler(req, res) {
  if (req.method === 'GET') {
    res.json({ data: 'ok' });
  }
  // POST, PUT, DELETE — no response returned!
}

// GOOD
export default function handler(req, res) {
  if (req.method === 'GET') {
    return res.json({ data: 'ok' });
  }
  return res.status(405).json({ error: 'Method not allowed' });
}
```

**P6: Ignoring function timeout limits**
```typescript
// BAD — no timeout awareness, function silently killed
export default async function handler(req, res) {
  const results = await processMillionRecords(); // Takes 5 minutes
  res.json(results);
}

// GOOD — chunk work, respect timeout
export default async function handler(req, res) {
  const batch = req.query.batch ?? 0;
  const results = await processBatch(batch, 100); // Process 100 at a time
  res.json({
    results,
    nextBatch: batch + 1,
    done: results.length < 100,
  });
}
```

**P7: Connection pool exhaustion**
```typescript
// BAD — each function instance creates its own connection pool
// With 100 concurrent functions × 10 pool connections = 1000 DB connections
const pool = new Pool({ max: 10 });

// GOOD — use a connection pooler
// Use Prisma Accelerate, PgBouncer, or Supabase connection pooler
// Configure pool size to 1-2 per function instance
const pool = new Pool({ max: 2 });
```

### Category 3: Edge Runtime Violations (High)

**P8: Node.js APIs in edge functions**
```typescript
// BAD — these crash silently in Edge Runtime
export const config = { runtime: 'edge' };

import fs from 'fs';           // Not available
import path from 'path';       // Not available
import crypto from 'crypto';   // Use crypto.subtle instead
import { Buffer } from 'buffer'; // Use Uint8Array instead

// GOOD — Web Standard APIs
const hash = await crypto.subtle.digest('SHA-256', data);
const encoded = btoa(String.fromCharCode(...new Uint8Array(hash)));
```
- **Detection:** `grep -rn "from 'fs'\|from 'path'\|from 'crypto'\|from 'child_process'" --include="*edge*" --include="*middleware*"`

**P9: Dynamic code evaluation in edge**
```typescript
// BAD — throws "Dynamic Code Evaluation not allowed"
export const config = { runtime: 'edge' };
const fn = new Function('return 42'); // Not allowed
eval('console.log("hi")');            // Not allowed

// GOOD — use static code only
const fn = () => 42;
```

### Category 4: Configuration Errors (Medium)

**P10: Missing environment variable scoping**
```bash
# BAD — variable only in Production, preview deployments break
vercel env add DATABASE_URL production

# GOOD — add to all environments that need it
vercel env add DATABASE_URL production preview development
```

**P11: Using deprecated builds property**
```json
// BAD (deprecated)
{
  "builds": [
    { "src": "api/**/*.ts", "use": "@vercel/node" }
  ]
}

// GOOD (current)
{
  "functions": {
    "api/**/*.ts": {
      "runtime": "nodejs20.x",
      "maxDuration": 30
    }
  }
}
```

**P12: Middleware running on static assets**
```typescript
// BAD — middleware runs on every request including static files
export function middleware(request) { /* auth check */ }

// GOOD — exclude static assets
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### Category 5: Cost Traps (Medium)

**P13: Uncached high-traffic endpoints**
```typescript
// BAD — every request invokes a function
export default function handler(req, res) {
  res.json({ config: getConfig() }); // No cache headers
}

// GOOD — cache at the edge, save function invocations
export default function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=86400');
  res.json({ config: getConfig() });
}
```

**P14: Over-allocated function memory**
```json
// BAD — 3GB for a simple JSON response
{
  "functions": { "api/config.ts": { "memory": 3008 } }
}

// GOOD — right-size per endpoint
{
  "functions": {
    "api/config.ts": { "memory": 128 },
    "api/image-process.ts": { "memory": 1024 }
  }
}
```

**P15: Middleware doing heavy work**
```typescript
// BAD — database query on every request
export async function middleware(request) {
  const user = await db.user.findUnique({ where: { id: token.sub } });
  // Runs on EVERY matched request, expensive at scale
}

// GOOD — validate JWT locally, no DB call
export function middleware(request) {
  const token = request.cookies.get('session')?.value;
  // Verify JWT signature locally (cheap, no external call)
}
```

## Quick Audit Script
```bash
#!/usr/bin/env bash
echo "=== Vercel Pitfall Audit ==="

echo "P1: Secrets in NEXT_PUBLIC_:"
grep -rn 'NEXT_PUBLIC_.*SECRET\|NEXT_PUBLIC_.*KEY\|NEXT_PUBLIC_.*TOKEN' src/ api/ 2>/dev/null || echo "  PASS"

echo "P2: Hardcoded credentials:"
grep -rnE 'sk_live|sk_test|Bearer [a-zA-Z0-9]{20,}' src/ api/ 2>/dev/null || echo "  PASS"

echo "P8: Node.js APIs in edge files:"
grep -rn "from 'fs'\|from 'path'\|from 'child_process'" src/middleware.ts api/*edge* 2>/dev/null || echo "  PASS"

echo "P11: Deprecated builds:"
jq -e '.builds' vercel.json 2>/dev/null && echo "  FAIL: deprecated builds" || echo "  PASS"

echo "P12: Middleware without matcher:"
grep -L 'matcher' src/middleware.ts 2>/dev/null && echo "  WARN: no matcher configured" || echo "  PASS"
```

## Output
- Anti-patterns identified and classified by severity (Critical/High/Medium)
- Security issues fixed and exposed secrets rotated
- Performance improvements from lazy initialization and caching
- ESLint and CI prevention measures blocking future regressions

## Error Handling
| Pitfall | Severity | Detection | Fix |
|---------|----------|-----------|-----|
| P1: NEXT_PUBLIC_ secrets | Critical | grep scan | Remove prefix, rotate secret |
| P4: Heavy cold starts | High | Cold start timing | Lazy initialization |
| P5: Missing response | High | 502 errors in logs | Return from all paths |
| P7: Connection exhaustion | High | DB connection errors | Use connection pooler |
| P8: Node.js in edge | High | EDGE_FUNCTION_INVOCATION_FAILED | Use Web APIs |
| P13: No cache headers | Medium | High function invocations bill | Add s-maxage |

## Resources
- [Vercel Best Practices](https://vercel.com/docs/best-practices)
- [Edge Runtime Limitations](https://vercel.com/docs/functions/runtimes/edge)
- [Function Configuration](https://vercel.com/docs/functions/configuring-functions)
- [Vercel Security](https://vercel.com/docs/security)
- [Vercel Limits](https://vercel.com/docs/limits)

## Next Steps
Return to `vercel-install-auth` for setup or `vercel-reference-architecture` for project structure.
