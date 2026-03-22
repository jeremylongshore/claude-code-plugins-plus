---
name: firecrawl-deploy-integration
description: |
  Deploy Firecrawl integrations to Vercel, Cloud Run, and Docker platforms.
  Use when deploying Firecrawl-powered applications to production,
  configuring platform-specific secrets, or setting up self-hosted Firecrawl.
  Trigger with phrases like "deploy firecrawl", "firecrawl Vercel",
  "firecrawl production deploy", "firecrawl Cloud Run", "firecrawl Docker".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(docker:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, deployment]

---
# Firecrawl Deploy Integration

## Overview
Deploy applications using Firecrawl's web scraping API to production. Covers Vercel serverless, Cloud Run containers, self-hosted Firecrawl via Docker, and webhook endpoint deployment for async crawl results.

## Prerequisites
- Firecrawl API key (`FIRECRAWL_API_KEY`)
- Application using `@mendable/firecrawl-js`
- Platform CLI (vercel, docker, or gcloud)

## Instructions

### Step 1: Configure Platform Secrets
```bash
set -euo pipefail
# Vercel
vercel env add FIRECRAWL_API_KEY production

# Cloud Run
echo -n "$FIRECRAWL_API_KEY" | gcloud secrets create firecrawl-api-key --data-file=-

# Docker
# Use --env-file or docker secrets
```

### Step 2: Vercel Serverless API Route
```typescript
// app/api/scrape/route.ts (Next.js App Router)
import FirecrawlApp from "@mendable/firecrawl-js";
import { NextRequest, NextResponse } from "next/server";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

export async function POST(req: NextRequest) {
  const { url, formats = ["markdown"] } = await req.json();

  if (!url) {
    return NextResponse.json({ error: "URL required" }, { status: 400 });
  }

  try {
    const result = await firecrawl.scrapeUrl(url, {
      formats,
      onlyMainContent: true,
      waitFor: 3000,
    });

    return NextResponse.json({
      success: result.success,
      markdown: result.markdown,
      title: result.metadata?.title,
      sourceURL: result.metadata?.sourceURL,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message, status: error.statusCode },
      { status: error.statusCode || 500 }
    );
  }
}
```

### Step 3: Self-Hosted Firecrawl (Docker Compose)
```yaml
# docker-compose.yml
services:
  firecrawl:
    image: mendableai/firecrawl:latest
    ports:
      - "3002:3002"
    environment:
      - PORT=3002
      - USE_DB_AUTHENTICATION=false
      - REDIS_URL=redis://redis:6379
      - REDIS_RATE_LIMIT_URL=redis://redis:6379
      - NUM_WORKERS_PER_QUEUE=2
      - BULL_AUTH_KEY=${BULL_AUTH_KEY:-changeme}
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - FIRECRAWL_API_KEY=fc-self-hosted
      - FIRECRAWL_API_URL=http://firecrawl:3002
    depends_on:
      - firecrawl
```

```typescript
// Point app to self-hosted Firecrawl
const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
  apiUrl: process.env.FIRECRAWL_API_URL || "https://api.firecrawl.dev",
});
```

### Step 4: Cloud Run Deployment
```bash
set -euo pipefail
# Build and deploy
gcloud run deploy firecrawl-app \
  --source . \
  --region us-central1 \
  --set-secrets "FIRECRAWL_API_KEY=firecrawl-api-key:latest" \
  --memory 512Mi \
  --timeout 300 \
  --allow-unauthenticated
```

### Step 5: Webhook Endpoint for Async Crawls
```typescript
// app/api/webhooks/firecrawl/route.ts
import crypto from "crypto";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.text();

  // Verify webhook signature
  const signature = req.headers.get("x-firecrawl-signature");
  if (signature && process.env.FIRECRAWL_WEBHOOK_SECRET) {
    const expected = crypto
      .createHmac("sha256", process.env.FIRECRAWL_WEBHOOK_SECRET)
      .update(body)
      .digest("hex");
    if (signature !== expected) {
      return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
    }
  }

  const { type, id, data } = JSON.parse(body);

  switch (type) {
    case "crawl.completed":
      console.log(`Crawl ${id} complete: ${data.length} pages`);
      await processPages(data);
      break;
    case "crawl.page":
      console.log(`Page scraped: ${data[0]?.metadata?.sourceURL}`);
      break;
    case "crawl.started":
      console.log(`Crawl ${id} started`);
      break;
  }

  return NextResponse.json({ received: true });
}
```

### Step 6: Health Check
```typescript
export async function GET() {
  try {
    const result = await firecrawl.scrapeUrl("https://example.com", {
      formats: ["markdown"],
    });
    return NextResponse.json({
      status: result.success ? "healthy" : "degraded",
    });
  } catch {
    return NextResponse.json({ status: "unhealthy" }, { status: 503 });
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Vercel timeout | Scrape takes > 10s | Use background functions or async crawl |
| Self-hosted OOM | Playwright browser memory | Increase container memory to 2GB+ |
| Cloud Run cold start | First request slow | Set min instances to 1 |
| Webhook not received | URL not publicly accessible | Use ngrok in dev, verify HTTPS in prod |

## Resources
- [Firecrawl Self-Hosting](https://docs.firecrawl.dev/contributing/self-host)
- [Firecrawl Webhooks](https://docs.firecrawl.dev/webhooks/overview)
- [Firecrawl Node SDK](https://docs.firecrawl.dev/sdks/node)

## Next Steps
For webhook handling, see `firecrawl-webhooks-events`.
