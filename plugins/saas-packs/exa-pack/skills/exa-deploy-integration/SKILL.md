---
name: exa-deploy-integration
description: |
  Deploy Exa integrations to Vercel, Docker, and Cloud Run platforms.
  Use when deploying Exa-powered applications to production,
  configuring platform-specific secrets, or building search API endpoints.
  Trigger with phrases like "deploy exa", "exa Vercel",
  "exa production deploy", "exa Cloud Run", "exa Docker".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, deployment, vercel, docker]

---
# Exa Deploy Integration

## Overview
Deploy applications using Exa's neural search API to production. Covers API endpoint creation, secret management per platform, caching for production traffic, and health check endpoints.

## Prerequisites
- Exa API key stored in `EXA_API_KEY` environment variable
- Application using `exa-js` SDK
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Vercel Edge Function
```typescript
// api/search.ts — Vercel API route
import Exa from "exa-js";

export const config = { runtime: "edge" };

export default async function handler(req: Request) {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const exa = new Exa(process.env.EXA_API_KEY!);
  const { query, numResults = 5 } = await req.json();

  if (!query || typeof query !== "string") {
    return Response.json({ error: "query is required" }, { status: 400 });
  }

  try {
    const results = await exa.searchAndContents(query, {
      type: "auto",
      numResults: Math.min(numResults, 20),
      text: { maxCharacters: 1000 },
      highlights: { maxCharacters: 300, query },
    });

    return Response.json({
      results: results.results.map(r => ({
        title: r.title,
        url: r.url,
        score: r.score,
        snippet: r.text?.substring(0, 300),
        highlights: r.highlights,
      })),
    });
  } catch (err: any) {
    const status = err.status || 500;
    return Response.json(
      { error: err.message, requestId: err.requestId },
      { status }
    );
  }
}
```

```bash
# Deploy to Vercel
vercel env add EXA_API_KEY production
vercel --prod
```

### Step 2: Docker Deployment
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```typescript
// src/server.ts — Express search API
import express from "express";
import Exa from "exa-js";

const app = express();
app.use(express.json());

const exa = new Exa(process.env.EXA_API_KEY!);

app.post("/api/search", async (req, res) => {
  const { query, numResults = 5, type = "auto" } = req.body;
  try {
    const results = await exa.searchAndContents(query, {
      type,
      numResults,
      text: { maxCharacters: 1000 },
    });
    res.json(results);
  } catch (err: any) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

app.get("/health", async (_req, res) => {
  try {
    await exa.search("health", { numResults: 1 });
    res.json({ status: "healthy", service: "exa" });
  } catch {
    res.status(503).json({ status: "unhealthy", service: "exa" });
  }
});

app.listen(3000, () => console.log("Listening on :3000"));
```

### Step 3: Google Cloud Run
```bash
set -euo pipefail
# Store API key in Secret Manager
echo -n "$EXA_API_KEY" | gcloud secrets create exa-api-key --data-file=-

# Deploy with secret mounted as env var
gcloud run deploy exa-search-api \
  --source . \
  --set-secrets=EXA_API_KEY=exa-api-key:latest \
  --allow-unauthenticated \
  --region us-central1
```

### Step 4: Production Search with Redis Cache
```typescript
import Exa from "exa-js";
import { Redis } from "ioredis";
import { createHash } from "crypto";

const exa = new Exa(process.env.EXA_API_KEY!);
const redis = new Redis(process.env.REDIS_URL!);

async function cachedSearch(query: string, opts: any = {}, ttl = 3600) {
  const key = `exa:${createHash("sha256").update(JSON.stringify({ query, ...opts })).digest("hex")}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const results = await exa.searchAndContents(query, {
    type: "auto",
    numResults: 5,
    text: { maxCharacters: 1000 },
    ...opts,
  });

  await redis.set(key, JSON.stringify(results), "EX", ttl);
  return results;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 401 in production | API key not set | Verify env var in deployment platform |
| Rate limited | Too many requests | Implement Redis cache + request queue |
| Slow responses | Large content requests | Reduce `maxCharacters` or `numResults` |
| Timeout on Edge | Query too complex | Use `type: "fast"` for edge functions |
| Cold start latency | Serverless cold start | Keep Exa client initialization outside handler |

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [exa-js SDK](https://github.com/exa-labs/exa-js)
- [Vercel Edge Functions](https://vercel.com/docs/functions/edge-functions)

## Next Steps
For multi-environment setup, see `exa-multi-env-setup`. For production checklist, see `exa-prod-checklist`.
