---
name: replit-rate-limits
description: |
  Handle Replit resource limits: KV database caps, deployment quotas, and request throttling.
  Use when hitting storage limits, managing deployment resources,
  or implementing rate limiting in your Replit-hosted app.
  Trigger with phrases like "replit rate limit", "replit throttling",
  "replit 429", "replit storage limit", "replit quota".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, api, limits, database]

---
# Replit Rate Limits

## Overview
Understand and work within Replit's resource limits: Key-Value Database size caps, Object Storage quotas, deployment compute budgets, and egress allowances. Implement rate limiting in your own app for production safety.

## Prerequisites
- Replit account with active Repls
- Understanding of your current resource usage
- For rate limiting: Express or Flask app

## Replit Platform Limits

### Key-Value Database
| Limit | Value |
|-------|-------|
| Total storage | 50 MiB (keys + values combined) |
| Maximum keys | 5,000 |
| Key size | 1,000 bytes |
| Value size | 5 MiB per value |

### Object Storage (App Storage)
| Limit | Value |
|-------|-------|
| Object size | Configurable per bucket |
| Bucket count | Per Repl (auto-provisioned) |
| Rate | Throttled at high request volume |

### PostgreSQL
| Limit | Value |
|-------|-------|
| Storage | Plan-dependent (1-10+ GB) |
| Connections | Pooled, plan-dependent |
| Dev + Prod | Separate databases auto-provisioned |

### Deployments
| Resource | Autoscale | Reserved VM |
|----------|-----------|-------------|
| Scale behavior | 0 to N based on traffic | Always-on, fixed size |
| Min cost | Pay per request | $0.20/day (~$6.20/month) |
| Max resources | Plan-dependent | Up to 4 vCPU, 16 GiB RAM |
| Egress | $0.10/GiB over allowance | $0.10/GiB over allowance |

## Instructions

### Step 1: Monitor KV Database Usage
```typescript
// Check how close you are to KV limits
import Database from '@replit/database';

async function checkKVUsage() {
  const db = new Database();
  const keys = await db.list();
  let totalSize = 0;

  for (const key of keys) {
    const value = await db.get(key);
    const valueSize = JSON.stringify(value).length;
    totalSize += key.length + valueSize;
  }

  const limitMiB = 50;
  const usedMiB = totalSize / (1024 * 1024);
  const percentUsed = (usedMiB / limitMiB * 100).toFixed(1);

  console.log(`KV Usage: ${usedMiB.toFixed(2)} MiB / ${limitMiB} MiB (${percentUsed}%)`);
  console.log(`Keys: ${keys.length} / 5,000`);

  if (parseFloat(percentUsed) > 80) {
    console.warn('WARNING: KV database above 80%. Consider migrating large values to Object Storage.');
  }
}
```

### Step 2: Implement App-Level Rate Limiting
```typescript
// src/middleware/rate-limit.ts — protect your Replit-hosted API
import { Request, Response, NextFunction } from 'express';

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

const store = new Map<string, RateLimitEntry>();

export function rateLimit(opts = { windowMs: 60000, max: 100 }) {
  return (req: Request, res: Response, next: NextFunction) => {
    const key = req.headers['x-replit-user-id'] as string || req.ip;
    const now = Date.now();
    const entry = store.get(key);

    if (!entry || now > entry.resetAt) {
      store.set(key, { count: 1, resetAt: now + opts.windowMs });
      setRateLimitHeaders(res, opts.max, opts.max - 1, now + opts.windowMs);
      return next();
    }

    entry.count++;
    const remaining = Math.max(0, opts.max - entry.count);
    setRateLimitHeaders(res, opts.max, remaining, entry.resetAt);

    if (entry.count > opts.max) {
      const retryAfter = Math.ceil((entry.resetAt - now) / 1000);
      res.set('Retry-After', String(retryAfter));
      return res.status(429).json({
        error: 'Too many requests',
        retryAfter,
      });
    }

    next();
  };
}

function setRateLimitHeaders(res: Response, limit: number, remaining: number, reset: number) {
  res.set('X-RateLimit-Limit', String(limit));
  res.set('X-RateLimit-Remaining', String(remaining));
  res.set('X-RateLimit-Reset', String(Math.ceil(reset / 1000)));
}

// Clean up expired entries periodically
setInterval(() => {
  const now = Date.now();
  for (const [key, entry] of store) {
    if (now > entry.resetAt) store.delete(key);
  }
}, 60000);
```

### Step 3: Apply Rate Limiting
```typescript
import express from 'express';
import { rateLimit } from './middleware/rate-limit';

const app = express();

// Global: 100 requests per minute
app.use(rateLimit({ windowMs: 60000, max: 100 }));

// Strict: 10 per minute for write operations
app.post('/api/*', rateLimit({ windowMs: 60000, max: 10 }));

// Generous: 500 per minute for reads
app.get('/api/*', rateLimit({ windowMs: 60000, max: 500 }));
```

### Step 4: Exponential Backoff for External APIs
```typescript
// When your Replit app calls external APIs
export async function withBackoff<T>(
  fn: () => Promise<T>,
  opts = { maxRetries: 5, baseMs: 1000, maxMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err: any) {
      if (attempt === opts.maxRetries) throw err;
      const status = err.status || err.response?.status;
      if (status && status !== 429 && status < 500) throw err;

      const delay = Math.min(opts.baseMs * 2 ** attempt, opts.maxMs);
      const jitter = Math.random() * delay * 0.1;
      await new Promise(r => setTimeout(r, delay + jitter));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 5: Request Queue for Burst Protection
```typescript
import PQueue from 'p-queue';

// Limit concurrent requests to external services
const queue = new PQueue({
  concurrency: 5,       // max parallel requests
  interval: 1000,       // per this window
  intervalCap: 10,      // max requests in window
});

async function rateLimitedFetch(url: string, opts?: RequestInit) {
  return queue.add(() => fetch(url, opts));
}
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| KV `Max storage exceeded` | Over 50 MiB | Migrate large values to Object Storage |
| KV `Max keys exceeded` | Over 5,000 keys | Archive old data, use prefix namespacing |
| 429 from your API | Client hitting your limits | Return `Retry-After` header |
| Object Storage throttled | Too many rapid requests | Add client-side request queue |
| High egress costs | Large responses | Compress, paginate, or cache at CDN |

## Resources
- [Replit Database](https://docs.replit.com/cloud-services/storage-and-databases/replit-database)
- [Usage-Based Billing](https://docs.replit.com/billing/about-usage-based-billing)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For security configuration, see `replit-security-basics`.
