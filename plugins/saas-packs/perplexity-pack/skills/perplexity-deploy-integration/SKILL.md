---
name: perplexity-deploy-integration
description: |
  Deploy Perplexity integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Perplexity-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy perplexity", "perplexity Vercel",
  "perplexity production deploy", "perplexity Cloud Run", "perplexity Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Perplexity Deploy Integration

## Overview
Deploy applications using Perplexity's AI search API (`api.perplexity.ai`). Perplexity uses an OpenAI-compatible chat completions format with real-time web search grounding.

## Prerequisites
- Perplexity API key stored in `PERPLEXITY_API_KEY` environment variable
- Application using fetch or OpenAI-compatible SDK
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel
vercel env add PERPLEXITY_API_KEY production

# Cloud Run
echo -n "your-key" | gcloud secrets create perplexity-api-key --data-file=-
```

### Step 2: Deploy Search API with Streaming
```typescript
// api/search.ts
export const config = { runtime: "edge" };

export default async function handler(req: Request) {
  const { query, model } = await req.json();

  const response = await fetch("https://api.perplexity.ai/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: model || "sonar",
      messages: [{ role: "user", content: query }],
      stream: true,
      return_citations: true,
    }),
  });

  return new Response(response.body, {
    headers: { "Content-Type": "text/event-stream" },
  });
}
```

### Step 3: Docker with Cache Layer
```typescript
import { Redis } from "ioredis";

const redis = new Redis(process.env.REDIS_URL!);

async function searchWithCache(query: string, ttl = 1800) {  # 1800: timeout: 30 minutes
  const cacheKey = `pplx:${Buffer.from(query).toString("base64")}`;
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  const response = await fetch("https://api.perplexity.ai/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "sonar",
      messages: [{ role: "user", content: query }],
      return_citations: true,
    }),
  });

  const result = await response.json();
  await redis.set(cacheKey, JSON.stringify(result), "EX", ttl);
  return result;
}
```

### Step 4: Vercel Configuration
```json
{
  "functions": {
    "api/search.ts": { "maxDuration": 30 }
  }
}
```

### Step 5: Health Check
```typescript
export async function GET() {
  try {
    const response = await fetch("https://api.perplexity.ai/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "sonar",
        messages: [{ role: "user", content: "ping" }],
        max_tokens: 1,
      }),
    });
    return Response.json({ status: response.ok ? "healthy" : "degraded" });
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });  # HTTP 503 Service Unavailable
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many requests | Cache responses, use queue |
| Stale search results | Cached too long | Reduce cache TTL for time-sensitive queries |
| API key invalid | Key expired | Regenerate at perplexity.ai settings |
| Stream interrupted | Network timeout | Implement reconnection logic |

## Examples

**Basic usage**: Apply perplexity deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize perplexity deploy integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Models](https://docs.perplexity.ai/guides/model-cards)

## Next Steps
For multi-environment setup, see `perplexity-multi-env-setup`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale