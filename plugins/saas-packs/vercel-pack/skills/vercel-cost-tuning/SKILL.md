---
name: vercel-cost-tuning
description: |
  Optimize Vercel costs through plan selection, function efficiency, and usage monitoring.
  Use when analyzing Vercel billing, reducing function execution costs,
  or implementing spend management and budget alerts.
  Trigger with phrases like "vercel cost", "vercel billing",
  "reduce vercel costs", "vercel pricing", "vercel expensive", "vercel budget".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, cost-optimization, billing, monitoring]

---
# Vercel Cost Tuning

## Overview
Optimize Vercel costs by understanding the Fluid Compute pricing model, reducing function execution time, leveraging edge caching to avoid function invocations, and configuring spend management. Covers plan comparison, cost drivers, and monitoring.

## Prerequisites
- Access to Vercel billing dashboard
- Understanding of current deployment architecture
- Access to Vercel Analytics for usage patterns

## Instructions

### Step 1: Understand the Pricing Model
Vercel uses **Fluid Compute** pricing (for new projects):

| Resource | Hobby (Free) | Pro ($20/member/mo) | Enterprise |
|----------|-------------|---------------------|------------|
| Bandwidth | 100 GB | 1 TB included | Custom |
| Serverless Execution | 100 GB-hrs | 1000 GB-hrs included | Custom |
| Edge Function invocations | 500K | 1M included | Custom |
| Edge Middleware invocations | 1M | 1M included | Custom |
| Image Optimizations | 1000 | 5000 included | Custom |
| Builds per day | 6000 | 6000 | Custom |
| Concurrent builds | 1 | 1 (more available) | Custom |

**Fluid Compute billing breakdown:**
- **Active CPU time**: charged per ms of actual CPU usage
- **Provisioned memory**: charged per GB-second of allocated memory
- Benefit: you pay for actual work, not idle waiting (e.g., waiting for a database response)

### Step 2: Identify Cost Drivers
```bash
# Check usage via API
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v2/usage" | jq .

# Top cost drivers on Vercel:
# 1. Serverless function execution time (CPU + memory)
# 2. Bandwidth (large responses, unoptimized images)
# 3. Edge Middleware invocations (runs on EVERY request)
# 4. Image optimizations (each unique transform costs)
# 5. Build minutes (frequent deploys or slow builds)
```

### Step 3: Reduce Function Execution Costs
```typescript
// 1. Right-size function memory — don't over-allocate
// vercel.json
{
  "functions": {
    "api/lightweight.ts": { "memory": 128 },    // Simple JSON responses
    "api/standard.ts": { "memory": 512 },       // Database queries
    "api/heavy.ts": { "memory": 1024 }          // Image processing
  }
}

// 2. Move read-only endpoints to Edge Functions (cheaper, no cold starts)
// api/config.ts
export const config = { runtime: 'edge' };
export default function handler() {
  return Response.json({ features: ['a', 'b'] });
}

// 3. Cache function responses at the edge
// Eliminates function invocations entirely for cached routes
export default function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=86400');
  res.json(data);
}
```

### Step 4: Reduce Bandwidth Costs
```json
// vercel.json — compress and cache aggressively
{
  "headers": [
    {
      "source": "/static/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ],
  "images": {
    "sizes": [640, 750, 1080],
    "formats": ["image/avif", "image/webp"],
    "minimumCacheTTL": 86400
  }
}
```

Key bandwidth reducers:
- Use Vercel's image optimization (auto WebP/AVIF conversion)
- Set aggressive cache headers on static assets
- Use ISR to serve static HTML instead of SSR
- Compress API responses (Vercel auto-compresses with Brotli)

### Step 5: Optimize Middleware Costs
Middleware runs on **every matched request**. Minimize its scope:

```typescript
// middleware.ts — scope to specific paths only
export const config = {
  matcher: [
    // Only run middleware on API routes and protected pages
    '/api/:path*',
    '/dashboard/:path*',
    // Skip static files, images, and public assets
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};

export function middleware(request) {
  // Keep logic minimal — this runs on every matched request
  // Avoid: database queries, external API calls, heavy computation
  // Good: cookie checks, header modifications, redirects
}
```

### Step 6: Configure Spend Management
In the Vercel dashboard under **Settings > Billing > Spend Management**:

```
Default budget: $200/month on-demand usage
Options:
- Set custom budget limit
- Enable hard limit (pauses all projects when reached)
- Configure email alerts at 50%, 75%, 90%, 100%
```

```bash
# Check current usage against budget via API
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v2/usage?teamId=team_xxx" \
  | jq '{period: .period, bandwidth: .bandwidth, execution: .serverlessFunctionExecution}'
```

## Cost Optimization Checklist

| Action | Impact | Effort |
|--------|--------|--------|
| Add `s-maxage` cache headers | High — eliminates function invocations | Low |
| Use Edge Functions for simple endpoints | Medium — cheaper than serverless | Low |
| Right-size function memory | Medium — reduces GB-hr cost | Low |
| Scope middleware matcher | Medium — reduces edge invocations | Low |
| Enable image optimization | Medium — reduces bandwidth | Low |
| Use ISR instead of SSR | High — serves cached HTML | Medium |
| Optimize build speed | Low — reduces build minutes | Medium |
| Set spend management alerts | Safety — prevents surprise bills | Low |

## Output
- Function memory right-sized per endpoint
- Edge caching reducing function invocations
- Middleware scoped to minimize invocations
- Spend management configured with budget alerts
- Usage monitoring via API

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Unexpected bill spike | Uncached high-traffic endpoint | Add `s-maxage` to the response |
| Projects paused | Hard spending limit reached | Increase limit or optimize usage |
| Image optimization quota exceeded | Too many unique image transforms | Reduce `sizes` array, increase cache TTL |
| Build minutes exceeded | Slow builds or too many deploys | Use `ignoreCommand` to skip non-code changes |

## Resources
- [Vercel Pricing](https://vercel.com/pricing)
- [Fluid Compute Pricing](https://vercel.com/docs/functions/usage-and-pricing)
- [Spend Management](https://vercel.com/docs/pricing#spend-management)
- [Limits](https://vercel.com/docs/limits)
- [Usage API](https://vercel.com/docs/rest-api)

## Next Steps
For reference architecture, see `vercel-reference-architecture`.
