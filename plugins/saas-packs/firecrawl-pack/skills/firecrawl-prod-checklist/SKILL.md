---
name: firecrawl-prod-checklist
description: |
  Execute Firecrawl production deployment checklist and rollback procedures.
  Use when deploying Firecrawl integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "firecrawl production", "deploy firecrawl",
  "firecrawl go-live", "firecrawl launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, deployment]

---
# Firecrawl Production Checklist

## Overview
Pre-deployment validation checklist for applications using Firecrawl's scrape, crawl, map, and extract APIs. Covers credential management, crawl safety limits, error handling, monitoring, and rollback.

## Prerequisites
- Staging environment tested and passing
- Production API key from [firecrawl.dev/app](https://firecrawl.dev/app)
- Monitoring infrastructure ready

## Pre-Deployment Checklist

### Credentials & Security
- [ ] Production `FIRECRAWL_API_KEY` in secure vault (not in code or .env)
- [ ] Key starts with `fc-` and is scoped to production
- [ ] Different API keys for dev/staging/production
- [ ] `.env` files in `.gitignore`
- [ ] Webhook secrets stored securely
- [ ] Git history scanned for leaked keys

### Crawl Safety
- [ ] All `crawlUrl` calls have `limit` parameter set
- [ ] `maxDepth` configured to prevent unbounded crawling
- [ ] `includePaths` / `excludePaths` filters applied where appropriate
- [ ] Credit budget tracking implemented (daily limit alerts)
- [ ] No hardcoded URLs in production code

### Error Handling
- [ ] 429 rate limit handling with exponential backoff
- [ ] 402 credit exhaustion handled gracefully (no crash)
- [ ] 401 auth failure logged and alerted
- [ ] Async crawl jobs have timeout with deadline
- [ ] Fallback from crawl to individual scrape on failure
- [ ] Empty markdown detection (JS rendering issues)

### Monitoring & Alerting
- [ ] Scrape success/failure rate tracked
- [ ] Credit consumption monitored
- [ ] Crawl job completion rate tracked
- [ ] Alert on credit balance below threshold
- [ ] Alert on error rate > 5%
- [ ] Webhook delivery failures logged

## Instructions

### Step 1: Verify API Connectivity
```bash
set -euo pipefail
# Test production key
curl -s https://api.firecrawl.dev/v1/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq '.success'

# Check credit balance
curl -s https://api.firecrawl.dev/v1/team/credits \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY_PROD" | jq .
```

### Step 2: Health Check Endpoint
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

export async function healthCheck() {
  const start = Date.now();
  try {
    const result = await firecrawl.scrapeUrl("https://example.com", {
      formats: ["markdown"],
    });
    return {
      status: result.success ? "healthy" : "degraded",
      latencyMs: Date.now() - start,
      hasContent: (result.markdown?.length || 0) > 0,
    };
  } catch (error: any) {
    return {
      status: "unhealthy",
      latencyMs: Date.now() - start,
      error: error.statusCode || error.message,
    };
  }
}
```

### Step 3: Production-Safe Crawl Wrapper
```typescript
export async function productionCrawl(url: string, opts: {
  maxPages: number;
  paths?: string[];
  timeout?: number;
}) {
  // Hard credit safety — never exceed configured limit
  const limit = Math.min(opts.maxPages, 500);

  const job = await firecrawl.asyncCrawlUrl(url, {
    limit,
    maxDepth: 3,
    includePaths: opts.paths,
    scrapeOptions: { formats: ["markdown"], onlyMainContent: true },
  });

  // Poll with timeout
  const deadline = Date.now() + (opts.timeout || 600000);
  let pollInterval = 2000;
  let status = await firecrawl.checkCrawlStatus(job.id);

  while (status.status === "scraping" && Date.now() < deadline) {
    await new Promise(r => setTimeout(r, pollInterval));
    pollInterval = Math.min(pollInterval * 1.5, 30000);
    status = await firecrawl.checkCrawlStatus(job.id);
  }

  if (status.status !== "completed") {
    throw new Error(`Crawl ${job.id} did not complete: ${status.status}`);
  }
  return status;
}
```

### Step 4: Rollback Procedure
```bash
set -euo pipefail
# Immediate rollback — disable Firecrawl integration
kubectl set env deployment/app FIRECRAWL_ENABLED=false
kubectl rollout restart deployment/app

# Verify rollback
curl -s https://app.example.com/health | jq '.services.firecrawl'
```

## Alerting Rules
| Alert | Condition | Severity |
|-------|-----------|----------|
| API unreachable | Health check fails 3x | P1 |
| Credits < 1000 | Balance check | P2 |
| Error rate > 5% | 429/5xx rate | P2 |
| Crawl timeout | Job stuck > 10min | P3 |
| Auth failure | Any 401 response | P1 |

## Resources
- [Firecrawl Dashboard](https://firecrawl.dev/app)
- [Firecrawl Rate Limits](https://docs.firecrawl.dev/rate-limits)
- [Firecrawl API Reference](https://docs.firecrawl.dev/api-reference/introduction)

## Next Steps
For version upgrades, see `firecrawl-upgrade-migration`.
