---
name: perplexity-deploy-integration
description: |
  Deploy Perplexity Sonar API integrations to Vercel, Cloud Run, and Docker.
  Use when deploying Perplexity-powered applications to production,
  configuring platform-specific secrets, or setting up edge functions.
  Trigger with phrases like "deploy perplexity", "perplexity Vercel",
  "perplexity production deploy", "perplexity Cloud Run", "perplexity Docker".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, deployment]

---
# Perplexity Deploy Integration

## Overview
Deploy applications using Perplexity Sonar API to edge and server platforms. Perplexity's OpenAI-compatible endpoint at `https://api.perplexity.ai/chat/completions` works from any platform that can make HTTPS requests.

## Prerequisites
- Perplexity API key stored in `PERPLEXITY_API_KEY`
- Platform CLI installed (vercel, gcloud, or docker)
- Application tested locally

## Instructions

### Step 1: Vercel Edge Function
```typescript
// api/search.ts
import OpenAI from "openai";

export const config = { runtime: "edge" };

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY!,
  baseURL: "https://api.perplexity.ai",
});

export default async function handler(req: Request) {
  const { query, model = "sonar", stream = false } = await req.json();

  if (stream) {
    const response = await perplexity.chat.completions.create({
      model,
      messages: [{ role: "user", content: query }],
      stream: true,
      max_tokens: 2048,
    });

    return new Response(response.toReadableStream(), {
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  const response = await perplexity.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
    max_tokens: 2048,
  });

  return Response.json({
    answer: response.choices[0].message.content,
    citations: (response as any).citations || [],
    model: response.model,
  });
}
```

```bash
set -euo pipefail
# Deploy to Vercel
vercel env add PERPLEXITY_API_KEY production
vercel deploy --prod
```

### Step 2: Cloud Run with Redis Cache
```typescript
// server.ts
import express from "express";
import OpenAI from "openai";
import { createClient } from "redis";
import { createHash } from "crypto";

const app = express();
app.use(express.json());

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY!,
  baseURL: "https://api.perplexity.ai",
});

const redis = createClient({ url: process.env.REDIS_URL });
await redis.connect();

app.post("/api/search", async (req, res) => {
  const { query, model = "sonar" } = req.body;
  const cacheKey = `pplx:${createHash("sha256").update(`${model}:${query}`).digest("hex")}`;

  // Check cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return res.json({ ...JSON.parse(cached), cached: true });
  }

  const response = await perplexity.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
    max_tokens: 2048,
  });

  const result = {
    answer: response.choices[0].message.content,
    citations: (response as any).citations || [],
    model: response.model,
    tokens: response.usage?.total_tokens,
  };

  // Cache for 1 hour
  await redis.setEx(cacheKey, 3600, JSON.stringify(result));
  res.json(result);
});

app.listen(8080);
```

```bash
set -euo pipefail
# Deploy to Cloud Run
gcloud secrets create perplexity-api-key --data-file=<(echo -n "$PERPLEXITY_API_KEY")
gcloud run deploy perplexity-search \
  --source . \
  --set-secrets=PERPLEXITY_API_KEY=perplexity-api-key:latest \
  --port=8080 \
  --allow-unauthenticated
```

### Step 3: Docker
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build

ENV NODE_ENV=production
EXPOSE 8080
CMD ["node", "dist/server.js"]
```

### Step 4: Vercel Configuration
```json
{
  "functions": {
    "api/search.ts": {
      "maxDuration": 30
    }
  }
}
```

### Step 5: Health Check
```typescript
app.get("/health", async (req, res) => {
  const start = Date.now();
  try {
    await perplexity.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: "ping" }],
      max_tokens: 5,
    });
    res.json({ status: "healthy", latencyMs: Date.now() - start });
  } catch {
    res.status(503).json({ status: "unhealthy", latencyMs: Date.now() - start });
  }
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Edge function timeout | sonar-pro takes >30s | Use sonar or increase maxDuration |
| Cache stale for news | TTL too long | Use `search_recency_filter` + shorter TTL |
| API key invalid after deploy | Wrong secret reference | Verify `vercel env ls` or `gcloud secrets` |
| Stream interrupted | Client disconnect | Handle abort signal gracefully |

## Output
- Deployed API endpoint serving Perplexity search
- Cached responses with configurable TTL
- Health check endpoint
- Platform-specific secret management

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Vercel Edge Functions](https://vercel.com/docs/functions/edge-functions)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps
For multi-environment setup, see `perplexity-multi-env-setup`.
