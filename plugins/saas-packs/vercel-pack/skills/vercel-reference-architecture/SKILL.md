---
name: vercel-reference-architecture
description: |
  Implement a Vercel reference architecture with layered project structure and best practices.
  Use when designing new Vercel projects, reviewing project structure,
  or establishing architecture standards for Vercel applications.
  Trigger with phrases like "vercel architecture", "vercel project structure",
  "vercel best practices layout", "how to organize vercel project".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, architecture, best-practices]

---
# Vercel Reference Architecture

## Overview
Implement a production-ready Vercel project architecture with clear separation across edge, server, and client layers. Covers directory structure, middleware patterns, API route organization, shared utilities, and configuration management.

## Prerequisites
- Understanding of Vercel's deployment model (edge, serverless, static)
- TypeScript project setup
- Next.js 14+ (recommended) or other Vercel-supported framework

## Instructions

### Step 1: Directory Structure
```
my-vercel-app/
├── public/                    # Static assets (served from CDN)
│   ├── favicon.ico
│   └── images/
├── src/
│   ├── app/                   # Next.js App Router pages
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   ├── api/               # API routes (serverless functions)
│   │   │   ├── health/route.ts
│   │   │   ├── users/route.ts
│   │   │   └── webhooks/
│   │   │       └── vercel/route.ts
│   │   ├── dashboard/         # Protected pages
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   └── (marketing)/       # Public pages (route group)
│   │       ├── pricing/page.tsx
│   │       └── about/page.tsx
│   ├── lib/                   # Shared utilities (server + client)
│   │   ├── api-client.ts      # External API wrapper
│   │   ├── db.ts              # Database client (lazy singleton)
│   │   ├── env.ts             # Typed environment variables
│   │   └── errors.ts          # Error classes
│   ├── components/            # React components
│   │   ├── ui/                # Design system primitives
│   │   └── features/          # Feature-specific components
│   └── middleware.ts          # Edge Middleware (auth, redirects)
├── vercel.json                # Vercel configuration
├── next.config.js             # Next.js configuration
├── tsconfig.json
├── package.json
└── .env.example               # Required env vars (no values)
```

### Step 2: Typed Environment Variables
```typescript
// src/lib/env.ts — validate env vars at import time
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  API_SECRET: z.string().min(16),
  NEXT_PUBLIC_API_URL: z.string().url(),
  VERCEL_ENV: z.enum(['production', 'preview', 'development']).default('development'),
  VERCEL_URL: z.string().optional(),
});

// Fails fast at startup if env vars are missing
export const env = envSchema.parse(process.env);

// Type-safe access throughout the app
// Usage: import { env } from '@/lib/env'; env.DATABASE_URL
```

### Step 3: Database Client (Lazy Singleton)
```typescript
// src/lib/db.ts — lazy init to minimize cold starts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient | undefined };

export const db = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.VERCEL_ENV === 'development' ? ['query'] : ['error'],
});

// Prevent multiple instances in development (hot reload)
if (process.env.VERCEL_ENV !== 'production') {
  globalForPrisma.prisma = db;
}
```

### Step 4: API Route Pattern
```typescript
// src/app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { env } from '@/lib/env';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = Number(searchParams.get('limit') ?? 20);

    const users = await db.user.findMany({ take: limit });
    return NextResponse.json({ users }, {
      headers: { 'Cache-Control': 's-maxage=60, stale-while-revalidate=300' },
    });
  } catch (error) {
    console.error('GET /api/users failed:', error);
    return NextResponse.json(
      { error: 'Internal server error', requestId: crypto.randomUUID() },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const user = await db.user.create({ data: body });
    return NextResponse.json({ user }, { status: 201 });
  } catch (error) {
    console.error('POST /api/users failed:', error);
    return NextResponse.json(
      { error: 'Failed to create user' },
      { status: 400 }
    );
  }
}
```

### Step 5: Edge Middleware for Auth
```typescript
// src/middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip auth for public routes
  if (pathname.startsWith('/api/health') || pathname.startsWith('/api/webhooks')) {
    return NextResponse.next();
  }

  // Check auth for dashboard routes
  if (pathname.startsWith('/dashboard') || pathname.startsWith('/api/')) {
    const token = request.cookies.get('session')?.value;
    if (!token) {
      if (pathname.startsWith('/api/')) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
      }
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### Step 6: Health Check Endpoint
```typescript
// src/app/api/health/route.ts
import { db } from '@/lib/db';

export const dynamic = 'force-dynamic'; // Never cache health checks

export async function GET() {
  const checks: Record<string, 'ok' | 'error'> = {};

  // Database connectivity
  try {
    await db.$queryRaw`SELECT 1`;
    checks.database = 'ok';
  } catch {
    checks.database = 'error';
  }

  const allHealthy = Object.values(checks).every(v => v === 'ok');

  return Response.json({
    status: allHealthy ? 'healthy' : 'degraded',
    checks,
    version: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? 'local',
    region: process.env.VERCEL_REGION ?? 'local',
    timestamp: new Date().toISOString(),
  }, {
    status: allHealthy ? 200 : 503,
  });
}
```

### Step 7: Vercel Configuration
```json
// vercel.json
{
  "regions": ["iad1"],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ],
  "rewrites": [
    { "source": "/docs/:path*", "destination": "https://docs.example.com/:path*" }
  ],
  "redirects": [
    { "source": "/old-page", "destination": "/new-page", "permanent": true }
  ]
}
```

## Layer Responsibilities

| Layer | Runtime | Responsibilities |
|-------|---------|-----------------|
| Edge (middleware.ts) | V8 isolates | Auth, redirects, A/B testing, headers |
| Server (api routes) | Node.js | Database queries, business logic, webhooks |
| Static (pages) | CDN | Pre-rendered pages, ISR, images |
| Client (components) | Browser | Interactivity, client state |

## Output
- Layered project structure with clear separation of concerns
- Typed environment variables validated at startup
- Lazy-initialized database client minimizing cold starts
- Edge Middleware handling authentication before server layer
- Health check endpoint for deployment verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Env validation fails on deploy | Missing required variable | Add to Vercel dashboard for target environment |
| Middleware runs on static assets | Matcher too broad | Add exclusions for `_next/static`, `_next/image` |
| Database connection pool exhausted | Too many concurrent functions | Use connection pooler (PgBouncer, Prisma Accelerate) |
| API route not found | Wrong directory structure | Must be in `src/app/api/` with `route.ts` filename |

## Resources
- [Next.js Project Structure](https://nextjs.org/docs/getting-started/project-structure)
- [Vercel Project Configuration](https://vercel.com/docs/project-configuration)
- [Middleware Documentation](https://vercel.com/docs/functions/edge-middleware)
- [API Routes (App Router)](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)

## Next Steps
For multi-environment setup, see `vercel-multi-env-setup`.
