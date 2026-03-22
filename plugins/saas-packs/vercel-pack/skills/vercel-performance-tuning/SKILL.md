---
name: vercel-performance-tuning
description: |
  Optimize Vercel deployment performance with caching, bundle optimization, and cold start reduction.
  Use when experiencing slow page loads, optimizing Core Web Vitals,
  or reducing serverless function cold start times.
  Trigger with phrases like "vercel performance", "optimize vercel",
  "vercel latency", "vercel caching", "vercel slow", "vercel cold start".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, performance, caching, optimization]

---
# Vercel Performance Tuning

## Overview
Optimize Vercel deployment performance across four levers: edge caching, bundle size reduction, serverless function cold start elimination, and Core Web Vitals improvement. Uses real Vercel cache headers, ISR, and Edge Functions for maximum performance.

## Prerequisites
- Vercel project deployed with accessible URL
- Access to Vercel Analytics (dashboard)
- Bundle analyzer available (`@next/bundle-analyzer` or similar)

## Instructions

### Step 1: Establish Performance Baseline
```bash
# Check deployment size and function count
vercel inspect https://my-app.vercel.app

# Run Lighthouse via CLI
npx lighthouse https://my-app.vercel.app --output=json --quiet \
  | jq '{performance: .categories.performance.score, lcp: .audits["largest-contentful-paint"].numericValue, cls: .audits["cumulative-layout-shift"].numericValue}'

# Check bundle size (Next.js)
ANALYZE=true npx next build
# Opens bundle analyzer report in browser
```

Enable Vercel Analytics in the dashboard under **Analytics** tab for ongoing monitoring.

### Step 2: Configure Edge Caching
```typescript
// api/cached-data.ts — cache API responses at the edge
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Cache at Vercel edge for 60s, serve stale for 300s while revalidating
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
  res.json({ data: fetchData(), cachedAt: new Date().toISOString() });
}
```

```json
// vercel.json — cache static assets aggressively
{
  "headers": [
    {
      "source": "/static/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/api/public-data",
      "headers": [
        { "key": "Cache-Control", "value": "s-maxage=3600, stale-while-revalidate=86400" }
      ]
    }
  ]
}
```

Cache header reference:
| Header | Effect |
|--------|--------|
| `s-maxage=N` | Cache at Vercel edge for N seconds |
| `stale-while-revalidate=N` | Serve stale while revalidating in background |
| `max-age=N` | Cache in browser for N seconds |
| `immutable` | Never revalidate (use with content-hashed filenames) |
| `no-cache` | Always revalidate (edge still caches) |
| `no-store` | Never cache anywhere |

### Step 3: Incremental Static Regeneration (ISR)
```typescript
// app/products/[id]/page.tsx (Next.js App Router)
export const revalidate = 60; // Revalidate every 60 seconds

export default async function ProductPage({ params }) {
  const product = await fetchProduct(params.id);
  return <ProductView product={product} />;
}

// Generate static pages at build time, regenerate on-demand
export async function generateStaticParams() {
  const products = await fetchTopProducts(100);
  return products.map(p => ({ id: p.id }));
}
```

On-demand revalidation via API route:
```typescript
// api/revalidate.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const secret = req.query.secret;
  if (secret !== process.env.REVALIDATION_SECRET) {
    return res.status(401).json({ error: 'Invalid secret' });
  }

  const path = req.query.path as string;
  await res.revalidate(path);
  res.json({ revalidated: true, path });
}
// Trigger: POST /api/revalidate?secret=xxx&path=/products/123
```

### Step 4: Reduce Cold Starts
```typescript
// Lazy initialization — don't import heavy modules at top level
// BAD: Cold start loads everything
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient(); // Runs on every cold start

// GOOD: Lazy singleton — only connects when first used
let prisma: PrismaClient | null = null;
function getDb(): PrismaClient {
  if (!prisma) {
    prisma = new PrismaClient();
  }
  return prisma;
}

export default async function handler(req, res) {
  const users = await getDb().user.findMany();
  res.json(users);
}
```

Move latency-critical paths to Edge Functions (zero cold starts):
```typescript
// api/fast.ts
export const config = { runtime: 'edge' };

export default function handler(request: Request) {
  return Response.json({ fast: true }); // No cold start, runs globally
}
```

### Step 5: Bundle Size Optimization
```javascript
// next.config.js — tree-shaking and optimization
module.exports = {
  experimental: {
    optimizePackageImports: ['lodash', '@mui/material', '@mui/icons-material'],
  },
  // Exclude server-only deps from client bundle
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = { fs: false, net: false, tls: false };
    }
    return config;
  },
};
```

```bash
# Find large dependencies
npx depcheck
npx cost-of-modules

# Replace heavy libraries with lighter alternatives
# moment.js (300KB) → dayjs (2KB)
# lodash (72KB) → lodash-es with tree-shaking
# axios (29KB) → native fetch
```

### Step 6: Image Optimization
```typescript
// Use Vercel's built-in image optimization
import Image from 'next/image';

// Automatic: resizes, converts to WebP/AVIF, caches at edge
<Image
  src="/hero.jpg"
  width={1200}
  height={600}
  alt="Hero"
  priority  // Preload for LCP
  sizes="(max-width: 768px) 100vw, 1200px"
/>
```

```json
// vercel.json — configure image optimization
{
  "images": {
    "sizes": [640, 750, 828, 1080, 1200],
    "domains": ["images.example.com"],
    "formats": ["image/avif", "image/webp"],
    "minimumCacheTTL": 86400
  }
}
```

## Performance Budget Reference

| Metric | Target | Vercel Tool |
|--------|--------|-------------|
| LCP | < 2.5s | Vercel Analytics |
| FID/INP | < 200ms | Vercel Analytics |
| CLS | < 0.1 | Vercel Analytics |
| TTFB | < 200ms | Edge caching |
| Function cold start | < 500ms | Lazy init / Edge Functions |
| Bundle size (gzipped) | < 200KB JS | Bundle analyzer |

## Output
- Edge caching configured with optimal cache-control headers
- ISR or on-demand revalidation for dynamic pages
- Cold starts eliminated via lazy initialization and Edge Functions
- Bundle size reduced through tree-shaking and import optimization
- Image optimization configured

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Cache not hitting | Missing `s-maxage` header | Add to response or vercel.json headers |
| ISR page always stale | `revalidate` set too high | Lower the revalidation interval |
| Large bundle warning | Importing entire library | Use specific imports: `import { map } from 'lodash-es'` |
| Cold start > 1s | Heavy top-level imports | Move to lazy initialization pattern |
| Images not optimized | External domain not whitelisted | Add to `images.domains` in config |

## Resources
- [Vercel Caching](https://vercel.com/docs/edge-network/caching)
- [ISR Documentation](https://vercel.com/docs/incremental-static-regeneration)
- [Vercel Analytics](https://vercel.com/docs/analytics)
- [Image Optimization](https://vercel.com/docs/image-optimization)
- [Function Configuration](https://vercel.com/docs/functions/configuring-functions)

## Next Steps
For cost optimization, see `vercel-cost-tuning`.
