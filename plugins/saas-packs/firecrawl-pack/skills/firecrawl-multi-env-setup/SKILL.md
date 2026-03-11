---
name: firecrawl-multi-env-setup
description: |
  Configure Firecrawl web scraping API across development, staging, and production environments.
  Use when setting up multi-environment scraping pipelines, managing credit budgets per env,
  or configuring different crawl limits and rate limits per deployment tier.
  Trigger with phrases like "firecrawl environments", "firecrawl staging",
  "firecrawl dev prod", "firecrawl environment setup", "firecrawl config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Multi-Environment Setup

## Overview
Firecrawl's credit-based pricing model makes environment separation critical. Development should use conservative crawl limits to avoid burning production credits during testing. A single uncapped development crawl can consume hundreds of credits. Separate API keys per environment allow independent credit pools and usage tracking. The key per-environment settings are: crawl limits, request concurrency, and whether to use Firecrawl Cloud vs self-hosted for dev/staging.

## Prerequisites
- Firecrawl account with API key from firecrawl.dev
- Optional: self-hosted Firecrawl instance for development
- Understanding of credit consumption model (1 credit = 1 page scraped)

## Environment Strategy

| Environment | API Key | Crawl Limit | Concurrency | Credit Budget |
|-------------|---------|-------------|-------------|---------------|
| Development | Dev key or self-hosted | 10 pages max | 1 | Minimal |
| Staging | Staging key | 100 pages max | 2 | Limited |
| Production | Prod key | Configured per task | Full | Monitored |

## Instructions

### Step 1: Configuration Structure
```typescript
// config/firecrawl.ts
import FirecrawlApp from "@mendable/firecrawl-js";

type Env = "development" | "staging" | "production";

interface FirecrawlConfig {
  apiKey: string;
  apiUrl?: string;              // override for self-hosted
  maxPagesPerCrawl: number;     // hard limit per crawl job
  maxDepth: number;
  concurrency: number;
  waitFor: number;              // ms to wait for JS rendering
}

const configs: Record<Env, FirecrawlConfig> = {
  development: {
    apiKey: process.env.FIRECRAWL_API_KEY_DEV || "fc-localdev",
    apiUrl: process.env.FIRECRAWL_API_URL_DEV, // point to self-hosted if available
    maxPagesPerCrawl: 10,         // strict limit in dev to protect credits
    maxDepth: 2,
    concurrency: 1,
    waitFor: 2000,
  },
  staging: {
    apiKey: process.env.FIRECRAWL_API_KEY_STAGING!,
    maxPagesPerCrawl: 100,
    maxDepth: 3,
    concurrency: 2,
    waitFor: 3000,
  },
  production: {
    apiKey: process.env.FIRECRAWL_API_KEY_PROD!,
    maxPagesPerCrawl: 500,        // per-task limit, set lower for specific jobs
    maxDepth: 5,
    concurrency: 5,
    waitFor: 3000,
  },
};

export function getFirecrawlConfig(): FirecrawlConfig {
  const env = (process.env.NODE_ENV || "development") as Env;
  return configs[env] || configs.development;
}

export function getFirecrawlClient(): FirecrawlApp {
  const cfg = getFirecrawlConfig();
  return new FirecrawlApp({
    apiKey: cfg.apiKey,
    ...(cfg.apiUrl ? { apiUrl: cfg.apiUrl } : {}),
  });
}
```

### Step 2: Self-Hosted Firecrawl for Development
```yaml
# docker-compose.dev.yml - Run Firecrawl locally in dev
version: "3.8"
services:
  firecrawl:
    image: mendableai/firecrawl:latest
    ports:
      - "3002:3002"
    environment:
      - USE_DB_AUTHENTICATION=false
      - PORT=3002
```
Set `FIRECRAWL_API_URL_DEV=http://localhost:3002` and any API key in `.env.local` to use local instance with no credit consumption.

### Step 3: Credit-Aware Scraping Wrapper
```typescript
// lib/firecrawl-service.ts
import { getFirecrawlClient, getFirecrawlConfig } from "../config/firecrawl";

export async function safeScrape(url: string, options?: any) {
  const firecrawl = getFirecrawlClient();
  const cfg = getFirecrawlConfig();

  return firecrawl.scrapeUrl(url, {
    formats: ["markdown"],
    onlyMainContent: true,
    waitFor: cfg.waitFor,
    ...options,
  });
}

export async function safeCrawl(url: string, customLimit?: number) {
  const firecrawl = getFirecrawlClient();
  const cfg = getFirecrawlConfig();

  const limit = Math.min(customLimit ?? cfg.maxPagesPerCrawl, cfg.maxPagesPerCrawl);

  return firecrawl.asyncCrawlUrl(url, {
    limit,
    maxDepth: cfg.maxDepth,
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });
}
```

### Step 4: Environment Variable Setup
```bash
# .env.local (development)
FIRECRAWL_API_KEY_DEV=fc-dev-abc123
FIRECRAWL_API_URL_DEV=http://localhost:3002  # optional self-hosted

# GitHub Actions - Staging environment
FIRECRAWL_API_KEY_STAGING=fc-staging-def456

# GitHub Actions - Production environment
FIRECRAWL_API_KEY_PROD=fc-prod-xyz789
```

### Step 5: CI/CD Pipeline Integration
```yaml
# .github/workflows/deploy.yml
jobs:
  test-scraping:
    environment: staging
    env:
      FIRECRAWL_API_KEY_STAGING: ${{ secrets.FIRECRAWL_API_KEY_STAGING }}
      NODE_ENV: staging
    steps:
      - run: node scripts/test-firecrawl.js
        # Uses staging config: 100-page limit, staging API key

  deploy:
    environment: production
    env:
      FIRECRAWL_API_KEY_PROD: ${{ secrets.FIRECRAWL_API_KEY_PROD }}
      NODE_ENV: production
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Credits depleted in dev | No page limit in dev config | Always set `maxPagesPerCrawl: 10` for development |
| Self-hosted not responding | Docker container not running | Check `docker-compose up firecrawl` |
| `402 Payment Required` | Production credits exhausted | Monitor credit balance before large jobs |
| Different results per env | `waitFor` mismatch | Standardize JS wait time or test with prod settings |

## Examples

### Check Active Configuration
```typescript
import { getFirecrawlConfig } from "./config/firecrawl";

const cfg = getFirecrawlConfig();
console.log(`Max pages: ${cfg.maxPagesPerCrawl}, depth: ${cfg.maxDepth}`);
console.log(`API URL: ${cfg.apiUrl || "https://api.firecrawl.dev"}`);
```

### Budget Check Before Large Crawl
```bash
# Check current credit balance
curl -s "https://api.firecrawl.dev/v1/team/credits" \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY_PROD" | jq .credits_remaining
```

## Resources
- [Firecrawl API Documentation](https://docs.firecrawl.dev)
- [Firecrawl Self-Hosting Guide](https://docs.firecrawl.dev/self-hosting)
- [Firecrawl Pricing](https://firecrawl.dev/pricing)

## Next Steps
For deployment configuration, see `firecrawl-deploy-integration`.
