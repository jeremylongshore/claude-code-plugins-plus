---
name: exa-deploy-integration
description: |
  Deploy Exa integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Exa-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy exa", "exa Vercel",
  "exa production deploy", "exa Cloud Run", "exa Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa Deploy Integration

## Overview
Deploy applications that use Exa's neural search API (`api.exa.ai`) to production. Covers API key management, deployment to Vercel and Docker, rate limit configuration, and caching strategies for search-heavy applications.

## Prerequisites
- Exa API key stored in `EXA_API_KEY` environment variable
- Application using `exa-js` SDK or REST API
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel
vercel env add EXA_API_KEY production

# Docker
echo "EXA_API_KEY=your-key" >> .env.production

# Cloud Run
echo -n "your-key" | gcloud secrets create exa-api-key --data-file=-
```

### Step 2: Vercel Edge Deployment
```typescript
// api/search.ts
import Exa from "exa-js";

export const config = { runtime: "edge" };

export default async function handler(req: Request) {
  const exa = new Exa(process.env.EXA_API_KEY!);
  const { query, numResults } = await req.json();

  const results = await exa.searchAndContents(query, {
    type: "neural",
    numResults: numResults || 5,
    text: { maxCharacters: 500 },  # HTTP 500 Internal Server Error
  });

  return Response.json(results);
}
```

### Step 3: Docker with Caching
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000  # 3000: 3 seconds in ms
CMD ["node", "dist/index.js"]
```

```typescript
// Search with Redis cache
import Exa from "exa-js";
import { Redis } from "ioredis";

const exa = new Exa(process.env.EXA_API_KEY!);
const redis = new Redis(process.env.REDIS_URL!);

async function cachedSearch(query: string, ttl = 3600) {  # 3600: timeout: 1 hour
  const cacheKey = `exa:${Buffer.from(query).toString("base64")}`;
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  const results = await exa.searchAndContents(query, {
    type: "neural",
    numResults: 5,
  });

  await redis.set(cacheKey, JSON.stringify(results), "EX", ttl);
  return results;
}
```

### Step 4: Health Check
```typescript
export async function GET() {
  try {
    const exa = new Exa(process.env.EXA_API_KEY!);
    await exa.search("test", { numResults: 1 });
    return Response.json({ status: "healthy" });
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });  # HTTP 503 Service Unavailable
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many requests | Implement caching and request queuing |
| Empty results | Query too specific | Broaden search terms |
| API key invalid | Key expired | Regenerate at dashboard.exa.ai |
| Timeout | Large content request | Reduce `maxCharacters` or `numResults` |

## Examples

### Deploy to Vercel
```bash
vercel env add EXA_API_KEY production && vercel --prod
```

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa JavaScript SDK](https://github.com/exa-labs/exa-js)

## Next Steps
For multi-environment setup, see `exa-multi-env-setup`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale