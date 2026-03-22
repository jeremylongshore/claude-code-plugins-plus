---
name: firecrawl-multi-env-setup
description: |
  Configure Firecrawl across development, staging, and production environments.
  Use when setting up multi-environment scraping pipelines, managing credit budgets per env,
  or configuring self-hosted Firecrawl for development.
  Trigger with phrases like "firecrawl environments", "firecrawl staging",
  "firecrawl dev prod", "firecrawl environment setup", "firecrawl config by env".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, deployment, api]

---
# Firecrawl Multi-Environment Setup

## Overview
Firecrawl's credit-based pricing makes environment separation critical. Development should use self-hosted Firecrawl or strict limits to avoid burning production credits during testing. This skill covers per-environment config, self-hosted Docker for dev, and credit budget enforcement.

## Environment Strategy

| Environment | API Source | Crawl Limit | Concurrency | Credits |
|-------------|-----------|-------------|-------------|---------|
| Development | Self-hosted Docker | 10 pages | 1 | Zero (local) |
| Staging | Cloud API (test key) | 50 pages | 2 | Limited |
| Production | Cloud API (prod key) | Per-task | Full plan | Monitored |

## Instructions

### Step 1: Environment-Aware Configuration
```typescript
// config/firecrawl.ts
import FirecrawlApp from "@mendable/firecrawl-js";

type Env = "development" | "staging" | "production";

interface FirecrawlConfig {
  apiKey: string;
  apiUrl?: string;
  maxPagesPerCrawl: number;
  maxDepth: number;
  concurrency: number;
  waitFor: number;
}

const configs: Record<Env, FirecrawlConfig> = {
  development: {
    apiKey: process.env.FIRECRAWL_API_KEY_DEV || "fc-localdev",
    apiUrl: process.env.FIRECRAWL_API_URL_DEV || "http://localhost:3002",
    maxPagesPerCrawl: 10,
    maxDepth: 2,
    concurrency: 1,
    waitFor: 2000,
  },
  staging: {
    apiKey: process.env.FIRECRAWL_API_KEY_STAGING!,
    maxPagesPerCrawl: 50,
    maxDepth: 3,
    concurrency: 2,
    waitFor: 3000,
  },
  production: {
    apiKey: process.env.FIRECRAWL_API_KEY_PROD!,
    maxPagesPerCrawl: 500,
    maxDepth: 5,
    concurrency: 5,
    waitFor: 3000,
  },
};

export function getConfig(): FirecrawlConfig {
  const env = (process.env.NODE_ENV || "development") as Env;
  return configs[env] || configs.development;
}

export function getFirecrawl(): FirecrawlApp {
  const cfg = getConfig();
  return new FirecrawlApp({
    apiKey: cfg.apiKey,
    ...(cfg.apiUrl ? { apiUrl: cfg.apiUrl } : {}),
  });
}
```

### Step 2: Self-Hosted Firecrawl for Development
```yaml
# docker-compose.dev.yml
services:
  firecrawl:
    image: mendableai/firecrawl:latest
    ports:
      - "3002:3002"
    environment:
      - PORT=3002
      - USE_DB_AUTHENTICATION=false
      - REDIS_URL=redis://redis:6379
      - NUM_WORKERS_PER_QUEUE=1
      - BULL_AUTH_KEY=devonly
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

```bash
set -euo pipefail
docker compose -f docker-compose.dev.yml up -d
# Verify: curl http://localhost:3002/health
```

### Step 3: Credit-Safe Scraping Wrapper
```typescript
// lib/firecrawl-service.ts
import { getFirecrawl, getConfig } from "../config/firecrawl";

export async function safeScrape(url: string, options?: any) {
  const firecrawl = getFirecrawl();
  return firecrawl.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,
    waitFor: getConfig().waitFor,
    ...options,
  });
}

export async function safeCrawl(url: string, customLimit?: number) {
  const firecrawl = getFirecrawl();
  const cfg = getConfig();
  const limit = Math.min(customLimit ?? cfg.maxPagesPerCrawl, cfg.maxPagesPerCrawl);

  return firecrawl.crawlUrl(url, {
    limit,
    maxDepth: cfg.maxDepth,
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });
}
```

### Step 4: Environment Variables
```bash
# .env.local (development — uses self-hosted, zero credits)
FIRECRAWL_API_KEY_DEV=fc-localdev
FIRECRAWL_API_URL_DEV=http://localhost:3002
NODE_ENV=development

# CI / Staging
FIRECRAWL_API_KEY_STAGING=fc-staging-xxx

# Production
FIRECRAWL_API_KEY_PROD=fc-prod-xxx
```

### Step 5: CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
jobs:
  test:
    environment: staging
    env:
      FIRECRAWL_API_KEY_STAGING: ${{ secrets.FIRECRAWL_API_KEY_STAGING }}
      NODE_ENV: staging
    steps:
      - run: npm ci && npm test
      - run: npm run test:integration
        # Uses staging config: 50-page limit, staging API key

  deploy:
    needs: test
    environment: production
    env:
      FIRECRAWL_API_KEY_PROD: ${{ secrets.FIRECRAWL_API_KEY_PROD }}
      NODE_ENV: production
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Dev credits drained | Using cloud API in dev | Point to self-hosted at localhost:3002 |
| Self-hosted not responding | Docker container down | `docker compose up -d firecrawl` |
| `402 Payment Required` | Prod credits exhausted | Monitor balance, set budget alerts |
| Different results per env | `waitFor` mismatch | Standardize wait time across envs |

## Examples

### Check Active Configuration
```typescript
import { getConfig } from "./config/firecrawl";

const cfg = getConfig();
console.log(`Env: ${process.env.NODE_ENV}`);
console.log(`Max pages: ${cfg.maxPagesPerCrawl}`);
console.log(`API: ${cfg.apiUrl || "https://api.firecrawl.dev"}`);
```

## Resources
- [Firecrawl Self-Hosting](https://docs.firecrawl.dev/contributing/self-host)
- [Firecrawl Pricing](https://firecrawl.dev/pricing)
- [Docker Compose](https://github.com/mendableai/firecrawl/blob/main/docker-compose.yaml)

## Next Steps
For deployment configuration, see `firecrawl-deploy-integration`.
