---
name: exa-multi-env-setup
description: |
  Configure Exa across development, staging, and production environments.
  Use when setting up multi-environment search pipelines, managing API key isolation,
  or configuring per-environment search limits and caching.
  Trigger with phrases like "exa environments", "exa staging", "exa dev prod",
  "exa environment setup", "exa multi-env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, deployment, api, environments]

---
# Exa Multi-Environment Setup

## Overview
Exa charges per search request at `api.exa.ai`. Multi-environment setup focuses on API key isolation per environment, request limits and caching to control costs in staging, and appropriate `numResults`/content settings per tier.

## Prerequisites
- Exa API key(s) from dashboard.exa.ai
- `exa-js` installed (`npm install exa-js`)
- Optional: Redis for search result caching in staging/production

## Environment Strategy

| Environment | Key Isolation | numResults | Content | Cache TTL |
|-------------|---------------|------------|---------|-----------|
| Development | Shared dev key | 3 | highlights only | None |
| Staging | Staging key | 5 | text (1000 chars) | 5 min |
| Production | Prod key | 10 | text (2000 chars) | 1 hour |

## Instructions

### Step 1: Environment-Aware Configuration
```typescript
// config/exa.ts
import Exa from "exa-js";

type Env = "development" | "staging" | "production";

interface ExaEnvConfig {
  apiKey: string;
  defaultNumResults: number;
  maxCharacters: number;
  searchType: "auto" | "neural" | "keyword";
  cacheEnabled: boolean;
  cacheTtlSeconds: number;
}

const configs: Record<Env, Omit<ExaEnvConfig, "apiKey"> & { keyVar: string }> = {
  development: {
    keyVar: "EXA_API_KEY",
    defaultNumResults: 3,
    maxCharacters: 500,
    searchType: "auto",
    cacheEnabled: false,
    cacheTtlSeconds: 0,
  },
  staging: {
    keyVar: "EXA_API_KEY_STAGING",
    defaultNumResults: 5,
    maxCharacters: 1000,
    searchType: "auto",
    cacheEnabled: true,
    cacheTtlSeconds: 300,  // 5 minutes
  },
  production: {
    keyVar: "EXA_API_KEY_PROD",
    defaultNumResults: 10,
    maxCharacters: 2000,
    searchType: "neural",
    cacheEnabled: true,
    cacheTtlSeconds: 3600,  // 1 hour
  },
};

export function getExaConfig(): ExaEnvConfig {
  const env = (process.env.NODE_ENV || "development") as Env;
  const config = configs[env] || configs.development;
  const apiKey = process.env[config.keyVar];
  if (!apiKey) {
    throw new Error(`${config.keyVar} not set for ${env} environment`);
  }
  return { ...config, apiKey };
}

export function getExaClient(): Exa {
  return new Exa(getExaConfig().apiKey);
}
```

### Step 2: Search Service with Config-Driven Defaults
```typescript
// lib/exa-search.ts
import { getExaClient, getExaConfig } from "../config/exa";

export async function search(query: string, numResults?: number) {
  const exa = getExaClient();
  const cfg = getExaConfig();
  const n = numResults ?? cfg.defaultNumResults;

  return exa.searchAndContents(query, {
    type: cfg.searchType,
    numResults: n,
    text: { maxCharacters: cfg.maxCharacters },
  });
}
```

### Step 3: Redis Cache Layer (Staging/Production)
```typescript
// lib/exa-cache.ts
import { Redis } from "ioredis";
import { getExaClient, getExaConfig } from "../config/exa";

const redis = process.env.REDIS_URL ? new Redis(process.env.REDIS_URL) : null;

export async function cachedSearch(query: string, numResults?: number) {
  const exa = getExaClient();
  const cfg = getExaConfig();
  const n = numResults ?? cfg.defaultNumResults;

  if (cfg.cacheEnabled && redis) {
    const cacheKey = `exa:${Buffer.from(`${query}:${n}:${cfg.searchType}`).toString("base64")}`;
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    const results = await exa.searchAndContents(query, {
      type: cfg.searchType,
      numResults: n,
      text: { maxCharacters: cfg.maxCharacters },
    });

    await redis.set(cacheKey, JSON.stringify(results), "EX", cfg.cacheTtlSeconds);
    return results;
  }

  return exa.searchAndContents(query, {
    type: cfg.searchType,
    numResults: n,
    text: { maxCharacters: cfg.maxCharacters },
  });
}
```

### Step 4: Environment Variables
```bash
# .env.local (development)
EXA_API_KEY=exa-dev-key-here

# .env.staging
EXA_API_KEY_STAGING=exa-staging-key-here
REDIS_URL=redis://staging-redis:6379

# .env.production
EXA_API_KEY_PROD=exa-prod-key-here
REDIS_URL=redis://prod-redis:6379
```

### Step 5: CI/CD Secret Configuration
```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    environment: staging
    env:
      EXA_API_KEY_STAGING: ${{ secrets.EXA_API_KEY_STAGING }}
      NODE_ENV: staging
    steps:
      - run: npm ci && npm run build && npm run deploy:staging

  deploy-production:
    environment: production
    env:
      EXA_API_KEY_PROD: ${{ secrets.EXA_API_KEY_PROD }}
      NODE_ENV: production
    steps:
      - run: npm ci && npm run build && npm run deploy:prod
```

### Step 6: Health Check Per Environment
```typescript
export async function checkExaHealth(): Promise<{
  status: string;
  env: string;
  latencyMs: number;
}> {
  const start = performance.now();
  try {
    const exa = getExaClient();
    await exa.search("health check", { numResults: 1 });
    return {
      status: "healthy",
      env: process.env.NODE_ENV || "development",
      latencyMs: Math.round(performance.now() - start),
    };
  } catch {
    return {
      status: "unhealthy",
      env: process.env.NODE_ENV || "development",
      latencyMs: Math.round(performance.now() - start),
    };
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Wrong API key for environment | Verify correct env var name |
| `429 rate_limit_exceeded` | Too many requests | Enable caching and request queuing |
| High API costs in staging | No caching enabled | Enable Redis cache with 5-min TTL |
| Empty results in dev | numResults too low | Increase from 3 to 5 |

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa Pricing](https://exa.ai/pricing)
- [exa-js SDK](https://github.com/exa-labs/exa-js)

## Next Steps
For deployment configuration, see `exa-deploy-integration`.
