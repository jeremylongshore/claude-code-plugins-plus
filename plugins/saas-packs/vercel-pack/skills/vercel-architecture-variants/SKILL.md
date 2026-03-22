---
name: vercel-architecture-variants
description: |
  Choose and implement Vercel architecture blueprints for different scales and use cases.
  Use when designing new Vercel projects, choosing between static, serverless, and edge architectures,
  or planning how to structure a multi-project Vercel deployment.
  Trigger with phrases like "vercel architecture", "vercel blueprint",
  "how to structure vercel", "vercel monorepo", "vercel multi-project".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, architecture, scaling, patterns]

---
# Vercel Architecture Variants

## Overview
Choose the right Vercel architecture based on team size, traffic patterns, and technical requirements. Covers five validated blueprints from static site to multi-project enterprise deployment, with migration paths between them.

## Prerequisites
- Understanding of team size and traffic requirements
- Knowledge of Vercel deployment model (edge, serverless, static)
- Clear SLA requirements

## Instructions

### Variant 1: Static Site (JAMstack)
**Best for:** Marketing sites, docs, blogs, landing pages
**Team size:** 1-3 developers
**Traffic:** Any (fully CDN-served)

```
project/
├── public/           # Static assets
├── src/
│   ├── pages/        # Static pages (SSG)
│   └── components/   # React components
├── vercel.json       # Headers, redirects
└── package.json
```

```json
// vercel.json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=3600, stale-while-revalidate=86400" }
      ]
    }
  ]
}
```

**Key decisions:**
- No serverless functions needed
- All pages pre-rendered at build time
- ISR for pages that update periodically
- Cost: minimal (mostly bandwidth)

### Variant 2: Full-Stack Next.js (Most Common)
**Best for:** SaaS applications, dashboards, e-commerce
**Team size:** 2-10 developers
**Traffic:** Low to high

```
project/
├── src/
│   ├── app/
│   │   ├── api/           # Serverless API routes
│   │   ├── (marketing)/   # Static public pages
│   │   └── dashboard/     # Dynamic authenticated pages
│   ├── lib/               # Shared utilities
│   ├── components/        # UI components
│   └── middleware.ts      # Edge auth + routing
├── prisma/                # Database schema
├── vercel.json
└── package.json
```

```json
// vercel.json
{
  "regions": ["iad1"],
  "functions": {
    "src/app/api/**/*.ts": {
      "maxDuration": 30,
      "memory": 1024
    }
  }
}
```

**Key decisions:**
- Mixed rendering: SSG for marketing, SSR for dashboard
- API routes in `app/api/` for backend logic
- Edge Middleware for auth (runs before every request)
- Database in same region as functions

### Variant 3: API-Only Backend
**Best for:** Mobile app backends, microservices, webhook processors
**Team size:** 1-5 developers
**Traffic:** API-driven

```
project/
├── api/                   # Serverless functions (one per route)
│   ├── users/
│   │   ├── index.ts       # GET/POST /api/users
│   │   └── [id].ts        # GET/PUT/DELETE /api/users/:id
│   ├── webhooks/
│   │   └── stripe.ts      # POST /api/webhooks/stripe
│   └── health.ts          # GET /api/health
├── lib/                   # Shared utilities
├── vercel.json
└── package.json
```

```json
// vercel.json
{
  "regions": ["iad1", "cdg1"],
  "rewrites": [
    { "source": "/v1/(.*)", "destination": "/api/$1" }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "https://myapp.com" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PUT,DELETE" }
      ]
    }
  ]
}
```

**Key decisions:**
- No frontend — pure API
- CORS headers for cross-origin access
- Version routing via rewrites (`/v1/*` → `/api/*`)
- Multi-region for global API latency

### Variant 4: Monorepo with Turborepo
**Best for:** Multiple related apps, shared component libraries
**Team size:** 5-20 developers
**Traffic:** Varies per app

```
monorepo/
├── apps/
│   ├── web/               # Main website (Vercel project 1)
│   │   ├── src/
│   │   ├── vercel.json
│   │   └── package.json
│   ├── docs/              # Documentation site (Vercel project 2)
│   │   ├── src/
│   │   ├── vercel.json
│   │   └── package.json
│   └── admin/             # Admin dashboard (Vercel project 3)
│       ├── src/
│       ├── vercel.json
│       └── package.json
├── packages/
│   ├── ui/                # Shared component library
│   ├── config/            # Shared ESLint, TS config
│   └── utils/             # Shared utilities
├── turbo.json
├── pnpm-workspace.yaml
└── package.json
```

Vercel auto-detects monorepos and builds only the affected app:

```json
// apps/web/vercel.json
{
  "ignoreCommand": "npx turbo-ignore"
}
```

Each app in `apps/` is a separate Vercel project with its own domain, env vars, and deployment settings.

### Variant 5: Multi-Zone Micro-Frontends (Enterprise)
**Best for:** Large organizations with independent teams
**Team size:** 20+ developers across multiple teams
**Traffic:** High

```
Each zone is an independent Vercel project:

Zone 1: marketing.company.com → Marketing team's Next.js app
Zone 2: app.company.com → Product team's Next.js app
Zone 3: docs.company.com → Docs team's Next.js app
Zone 4: api.company.com → Platform team's API-only project

Main project uses multi-zones (next.config.js):
```

```javascript
// Main app: next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/docs/:path*',
        destination: 'https://docs.company.com/docs/:path*',
      },
      {
        source: '/blog/:path*',
        destination: 'https://marketing.company.com/blog/:path*',
      },
    ];
  },
};
```

**Key decisions:**
- Independent deploy cycles per team
- Shared auth via Edge Middleware or external IdP
- Consistent design system via shared npm packages
- Each zone has its own env vars and scaling

## Architecture Decision Matrix

| Factor | Static | Full-Stack | API-Only | Monorepo | Multi-Zone |
|--------|--------|-----------|----------|----------|------------|
| Team size | 1-3 | 2-10 | 1-5 | 5-20 | 20+ |
| Deploy independence | N/A | Single | Single | Per-app | Per-team |
| Frontend | Yes | Yes | No | Yes | Yes |
| Database | No | Yes | Yes | Per-app | Per-zone |
| Complexity | Low | Medium | Low | Medium | High |
| Cost | Low | Medium | Low | Medium | High |

## Migration Path

```
Static Site → Full-Stack Next.js → Monorepo → Multi-Zone
     ↑              ↑                  ↑           ↑
   Start here    Add API routes    Add shared    Split teams
                 Add auth          packages      Independent
                 Add database                    deployments
```

## Output
- Architecture variant selected based on team size and requirements
- Project structure implemented following the chosen blueprint
- Vercel configuration optimized for the architecture
- Migration path documented for future scaling

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Monorepo builds all apps | Missing `ignoreCommand` | Add `npx turbo-ignore` |
| Multi-zone routing conflict | Overlapping paths | Ensure rewrites don't conflict |
| Shared package not found | pnpm workspace misconfigured | Check `pnpm-workspace.yaml` includes |
| API-only 404 on root | No `public/index.html` | Add a minimal index or redirect |

## Resources
- [Vercel Monorepos](https://vercel.com/docs/monorepos)
- [Turborepo on Vercel](https://vercel.com/docs/monorepos/turborepo)
- [Next.js Multi-Zones](https://nextjs.org/docs/app/building-your-application/deploying/multi-zones)
- [Vercel Project Structure](https://vercel.com/docs/project-configuration)

## Next Steps
For known pitfalls and anti-patterns, see `vercel-known-pitfalls`.
