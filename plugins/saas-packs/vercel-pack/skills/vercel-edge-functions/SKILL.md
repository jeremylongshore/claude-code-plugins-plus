---
name: vercel-edge-functions
description: |
  Build and deploy Vercel Edge Functions for ultra-low latency at the edge.
  Use when creating API routes with minimal latency, geolocation-based routing,
  A/B testing, or authentication at the edge.
  Trigger with phrases like "vercel edge function", "vercel edge runtime",
  "deploy edge function", "vercel middleware", "@vercel/edge".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, edge, serverless, performance]

---
# Vercel Edge Functions

## Overview
Edge Functions run on Vercel's Edge Network (V8 isolates) close to the user with no cold starts. They use Web Standard APIs (Request, Response, fetch) instead of Node.js APIs. Ideal for authentication, A/B testing, geolocation routing, and low-latency API responses.

## Prerequisites
- Completed `vercel-install-auth` setup
- Familiarity with Web APIs (Request/Response)
- Node.js 18+ for local development

## Instructions

### Step 1: Create an Edge Function
```typescript
// api/edge-hello.ts
// Export `runtime = 'edge'` to run on the Edge Runtime
export const config = { runtime: 'edge' };

export default function handler(request: Request): Response {
  return new Response(
    JSON.stringify({
      message: 'Hello from the Edge!',
      region: request.headers.get('x-vercel-ip-city') ?? 'unknown',
      timestamp: Date.now(),
    }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}
```

### Step 2: Edge Function with Geolocation
Vercel injects geolocation headers into every edge request:

```typescript
// api/geo.ts
export const config = { runtime: 'edge' };

export default function handler(request: Request): Response {
  const city = request.headers.get('x-vercel-ip-city') ?? 'unknown';
  const country = request.headers.get('x-vercel-ip-country') ?? 'unknown';
  const region = request.headers.get('x-vercel-ip-country-region') ?? 'unknown';
  const latitude = request.headers.get('x-vercel-ip-latitude');
  const longitude = request.headers.get('x-vercel-ip-longitude');

  return Response.json({
    city: decodeURIComponent(city),
    country,
    region,
    coordinates: latitude && longitude ? { lat: latitude, lng: longitude } : null,
  });
}
```

### Step 3: Edge Middleware (middleware.ts)
Middleware runs before every request and can rewrite, redirect, or add headers:

```typescript
// middleware.ts (must be at project root or src/)
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // Example 1: Redirect based on country
  const country = request.geo?.country ?? 'US';
  if (country === 'DE') {
    return NextResponse.redirect(new URL('/de', request.url));
  }

  // Example 2: A/B testing with cookies
  const bucket = request.cookies.get('ab-bucket')?.value;
  if (!bucket) {
    const response = NextResponse.next();
    response.cookies.set('ab-bucket', Math.random() > 0.5 ? 'a' : 'b');
    return response;
  }

  // Example 3: Add security headers
  const response = NextResponse.next();
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  return response;
}

// Only run on specific paths — skip static assets
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### Step 4: Edge Function with Streaming
```typescript
// api/stream.ts
export const config = { runtime: 'edge' };

export default function handler(): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      for (let i = 0; i < 5; i++) {
        controller.enqueue(encoder.encode(`data: chunk ${i}\n\n`));
        await new Promise(r => setTimeout(r, 500));
      }
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
```

### Step 5: Edge Config (Key-Value Store)
```typescript
// api/feature-flags.ts
import { get } from '@vercel/edge-config';

export const config = { runtime: 'edge' };

export default async function handler(): Promise<Response> {
  // Read from Edge Config — sub-millisecond reads at the edge
  const maintenanceMode = await get<boolean>('maintenance_mode');
  const featureFlags = await get<Record<string, boolean>>('feature_flags');

  if (maintenanceMode) {
    return Response.json({ status: 'maintenance' }, { status: 503 });
  }

  return Response.json({ features: featureFlags });
}
```

Install: `npm install @vercel/edge-config`

## Edge vs Serverless Comparison

| Feature | Edge Runtime | Node.js (Serverless) |
|---------|-------------|---------------------|
| Cold start | None (~0ms) | 250ms–1s+ |
| Max duration | 30s (Hobby), 5min (Pro) | 10s (Hobby), 5min (Pro) |
| Max size | 1 MB (after gzip) | 250 MB (unzipped) |
| APIs available | Web Standard APIs | Full Node.js API |
| npm packages | Limited (no native modules) | All npm packages |
| Global deployment | Automatic | Single region default |
| Use case | Auth, routing, A/B, geo | Database queries, heavy compute |

## Available Web APIs in Edge Runtime
`fetch`, `Request`, `Response`, `Headers`, `URL`, `URLSearchParams`, `TextEncoder`, `TextDecoder`, `ReadableStream`, `WritableStream`, `TransformStream`, `crypto`, `atob`, `btoa`, `structuredClone`, `setTimeout`, `setInterval`, `AbortController`

**NOT available**: `fs`, `path`, `child_process`, `net`, `http`, `dns`, native Node.js modules

## Output
- Edge Function deployed globally with zero cold starts
- Geolocation-based routing using Vercel's injected headers
- Middleware running authentication and A/B tests at the edge
- Streaming responses for real-time data delivery

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `EDGE_FUNCTION_INVOCATION_FAILED` | Runtime error in edge function | Check logs — no `try/catch` around async code |
| `Dynamic Code Evaluation not allowed` | Using `eval()` or `new Function()` | Refactor to avoid dynamic code evaluation |
| `Module not found` | npm package uses Node.js APIs | Use edge-compatible alternative or switch to Node.js runtime |
| `FUNCTION_PAYLOAD_TOO_LARGE` | Edge function bundle > 1 MB | Tree-shake imports, split into smaller functions |
| `TypeError: x is not a function` | Node.js API used in edge runtime | Replace with Web Standard API equivalent |

## Resources
- [Edge Functions Documentation](https://vercel.com/docs/functions/runtimes/edge)
- [Edge Middleware](https://vercel.com/docs/functions/edge-middleware)
- [Edge Config](https://vercel.com/docs/edge-config)
- [Edge Runtime API](https://vercel.com/docs/functions/runtimes/edge)
- [Vercel Geolocation Headers](https://vercel.com/docs/headers/request-headers)

## Next Steps
For common errors, see `vercel-common-errors`.
