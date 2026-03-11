---
name: firecrawl-deploy-integration
description: |
  Deploy FireCrawl integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying FireCrawl-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy firecrawl", "firecrawl Vercel",
  "firecrawl production deploy", "firecrawl Cloud Run", "firecrawl Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Firecrawl Deploy Integration

## Overview
Deploy applications using Firecrawl's web scraping API (`api.firecrawl.dev`) to production. Covers API key management, webhook endpoint deployment for async crawl results, and self-hosted Firecrawl deployment options using Docker.

## Prerequisites
- Firecrawl API key stored in `FIRECRAWL_API_KEY` environment variable
- Application using `@mendable/firecrawl-js` SDK
- Platform CLI installed (vercel, docker, or gcloud)
- Webhook endpoint for async crawl results

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel
vercel env add FIRECRAWL_API_KEY production

# Cloud Run
echo -n "your-key" | gcloud secrets create firecrawl-api-key --data-file=-
```

### Step 2: Deploy Scraping API
```typescript
// api/scrape.ts
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

export async function POST(req: Request) {
  const { url, formats } = await req.json();

  const result = await firecrawl.scrapeUrl(url, {
    formats: formats || ["markdown"],
  });

  return Response.json({
    markdown: result.markdown,
    metadata: result.metadata,
  });
}
```

### Step 3: Self-Hosted Firecrawl (Docker)
```yaml
# docker-compose.yml
version: "3.8"
services:
  firecrawl:
    image: mendableai/firecrawl:latest
    ports:
      - "3002:3002"
    environment:
      - REDIS_URL=redis://redis:6379
      - PLAYWRIGHT_BROWSERS_PATH=/browsers
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - FIRECRAWL_API_URL=http://firecrawl:3002
    depends_on:
      - firecrawl
```

### Step 4: Webhook Endpoint for Async Crawls
```typescript
// api/webhooks/firecrawl.ts
export async function POST(req: Request) {
  const { type, id, data } = await req.json();

  if (type === "crawl.completed") {
    await processScrapedPages(id, data.pages);
  }

  return Response.json({ received: true });
}
```

### Step 5: Health Check
```typescript
export async function GET() {
  try {
    const result = await firecrawl.scrapeUrl("https://example.com", {
      formats: ["markdown"],
    });
    return Response.json({ status: result ? "healthy" : "degraded" });
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many scrape requests | Queue requests with delays |
| Scrape blocked | Target site protection | Use `waitFor` and browser options |
| API key invalid | Key expired | Regenerate at firecrawl.dev dashboard |
| Self-hosted memory | Playwright overhead | Increase container memory to 2GB+ |

## Examples

### Quick Deploy
```bash
vercel env add FIRECRAWL_API_KEY production && vercel --prod
```

## Resources
- [Firecrawl Documentation](https://docs.firecrawl.dev)
- [Firecrawl Self-Hosting](https://docs.firecrawl.dev/self-hosting)

## Next Steps
For webhook handling, see `firecrawl-webhooks-events`.
