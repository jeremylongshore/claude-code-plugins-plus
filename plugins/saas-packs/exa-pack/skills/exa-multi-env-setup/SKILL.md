---
name: exa-multi-env-setup
description: |
  Configure Exa neural search API across development, staging, and production environments.
  Use when setting up multi-environment search pipelines, managing API key isolation,
  or configuring caching and result limits per deployment tier.
  Trigger with phrases like "exa environments", "exa staging", "exa dev prod",
  "exa environment setup", "exa api key by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Multi-Environment Setup

## Overview
Exa's neural search API (`api.exa.ai`) charges per search request. Multi-environment setup focuses on API key isolation, request caching to reduce costs in staging/production, and controlling `numResults` and `text.maxCharacters` per environment (higher values cost more). Development can use a shared low-quota key; production needs its own key with appropriate rate limits and Redis caching to avoid re-fetching identical queries.

## Prerequisites
- Exa API key(s) from dashboard.exa.ai
- `exa-js` npm package (`npm install exa-js`)
- Optional: Redis for search result caching in staging/production

## Environment Strategy

| Environment | Key Isolation | numResults | Cache TTL | Rate Limit |
|-------------|---------------|------------|-----------|------------|
| Development | Shared dev key | 3 (low cost) | None | Low |
| Staging | Staging key | 5 | 5 minutes | Moderate |
| Production | Prod key | 5-10 per query | 1 hour | Full |

## Instructions

### Step 1: Configuration Structure
```typescript
// config/exa.ts
import Exa from "exa-js";

type Env = "development" | "staging" | "production";

interface ExaConfig {
  apiKey: string;
  defaultNumResults: number;
  maxCharacters: number;       // per result content length
  cacheEnabled: boolean;
  cacheTtlSeconds: number;
}

const configs: Record<Env, ExaConfig> = {
  development: {
    apiKey: process.env.EXA_API_KEY!,
    defaultNumResults: 3,       // fewer results = lower cost in dev
    maxCharacters: 500,
    cacheEnabled: false,        // don't bother caching in dev
    cacheTtlSeconds: 0,
  },
  staging: {
    apiKey: process.env.EXA_API_KEY_STAGING!,
    defaultNumResults: 5,
    maxCharacters: 1000,
    cacheEnabled: true,
    cacheTtlSeconds: 300,       // 5-minute cache in staging
  },
  production: {
    apiKey: process.env.EXA_API_KEY_PROD!,
    defaultNumResults: 5,
    maxCharacters: 1000,
    cacheEnabled: true,
    cacheTtlSeconds: 3600,      // 1-hour cache for repeated queries
  },
};

export function getExaConfig(): ExaConfig {
  const env = (process.env.NODE_ENV || "development") as Env;
  const config = configs[env] || configs.development;
  if (!config.apiKey) {
    throw new Error(`EXA_API_KEY not set for ${env} environment`);
  }
  return config;
}

export function getExaClient(): Exa {
  return new Exa(getExaConfig().apiKey);
}
```

### Step 2: Search Service with Caching
```typescript
// lib/exa-search.ts
import { getExaClient, getExaConfig } from "../config/exa";
import { Redis } from "ioredis";

const redis = process.env.REDIS_URL ? new Redis(process.env.REDIS_URL) : null;

export async function search(query: string, numResults?: number) {
  const exa = getExaClient();
  const cfg = getExaConfig();
  const n = numResults ?? cfg.defaultNumResults;

  // Check cache if enabled
  if (cfg.cacheEnabled && redis) {
    const cacheKey = `exa:${Buffer.from(`${query}:${n}`).toString("base64")}`;
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    const results = await exa.searchAndContents(query, {
      type: "neural",
      numResults: n,
      text: { maxCharacters: cfg.maxCharacters },
    });

    await redis.set(cacheKey, JSON.stringify(results), "EX", cfg.cacheTtlSeconds);
    return results;
  }

  return exa.searchAndContents(query, {
    type: "neural",
    numResults: n,
    text: { maxCharacters: cfg.maxCharacters },
  });
}
```

### Step 3: Environment Variable Setup
```bash
# .env.local (development)
EXA_API_KEY=exa-dev-abc123

# GitHub Actions - Staging
EXA_API_KEY_STAGING=exa-staging-def456

# GitHub Actions - Production
EXA_API_KEY_PROD=exa-prod-xyz789
REDIS_URL=redis://prod-redis:6379
```

### Step 4: Health Check Per Environment
```typescript
// lib/exa-health.ts
export async function checkExaHealth(): Promise<{ status: string; env: string }> {
  try {
    const exa = getExaClient();
    await exa.search("test connectivity", { numResults: 1 });
    return { status: "healthy", env: process.env.NODE_ENV || "development" };
  } catch (err: any) {
    return { status: "unhealthy", env: process.env.NODE_ENV || "development" };
  }
}
```

### Step 5: CI/CD Configuration
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      EXA_API_KEY_STAGING: ${{ secrets.EXA_API_KEY_STAGING }}
      NODE_ENV: staging
    steps:
      - run: npm run build && npm run deploy:staging

  deploy-production:
    environment: production
    env:
      EXA_API_KEY_PROD: ${{ secrets.EXA_API_KEY_PROD }}
      NODE_ENV: production
    steps:
      - run: npm run deploy:prod
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Wrong API key for environment | Verify `EXA_API_KEY` in env vars |
| `429 rate_limit_exceeded` | Too many requests | Implement caching and request queuing |
| High API costs in staging | No caching enabled | Enable Redis cache with 5-minute TTL |
| Empty results | Query too narrow | Broaden query terms for neural search |

## Examples

### Check Active Configuration
```typescript
import { getExaConfig } from "./config/exa";

const cfg = getExaConfig();
console.log(`Results per query: ${cfg.defaultNumResults}`);
console.log(`Cache enabled: ${cfg.cacheEnabled}, TTL: ${cfg.cacheTtlSeconds}s`);
```

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa JavaScript SDK](https://github.com/exa-labs/exa-js)
- [Exa Pricing](https://exa.ai/pricing)

## Next Steps
For deployment configuration, see `exa-deploy-integration`.
