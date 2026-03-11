---
name: mistral-deploy-integration
description: |
  Deploy Mistral AI integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Mistral AI-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy mistral", "mistral Vercel",
  "mistral production deploy", "mistral Cloud Run", "mistral Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Mistral AI Deploy Integration

## Overview
Deploy Mistral AI-powered applications to production with proper API key management, model endpoint configuration, and platform-specific optimizations. Covers Vercel, Docker, and Cloud Run deployments with the Mistral SDK connecting to `api.mistral.ai`.

## Prerequisites
- Mistral AI API key for production use
- Platform CLI installed (vercel, docker, or gcloud)
- Application using `@mistralai/mistralai` SDK
- Environment variables documented

## Instructions

### Step 1: Configure Environment Variables
```bash
# Vercel
vercel env add MISTRAL_API_KEY production
vercel env add MISTRAL_MODEL production  # e.g., mistral-large-latest

# Docker
echo "MISTRAL_API_KEY=your-key" > .env.production

# Cloud Run
gcloud secrets create mistral-api-key --data-file=- <<< "your-key"
```

### Step 2: Docker Deployment
```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Step 3: Vercel Serverless Configuration
```json
{
  "functions": {
    "api/chat.ts": {
      "maxDuration": 60
    }
  },
  "env": {
    "MISTRAL_API_KEY": "@mistral_api_key"
  }
}
```

```typescript
// api/chat.ts - Vercel Edge Function
import Mistral from "@mistralai/mistralai";

export const config = { runtime: "edge" };

export default async function handler(req: Request) {
  const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });
  const { messages } = await req.json();

  const response = await client.chat.complete({
    model: process.env.MISTRAL_MODEL || "mistral-small-latest",
    messages,
  });

  return Response.json(response);
}
```

### Step 4: Cloud Run Deployment
```bash
gcloud run deploy mistral-service \
  --image gcr.io/$PROJECT_ID/mistral-app \
  --region us-central1 \
  --platform managed \
  --set-secrets=MISTRAL_API_KEY=mistral-api-key:latest \
  --set-env-vars=MISTRAL_MODEL=mistral-large-latest \
  --min-instances=1 \
  --max-instances=10
```

### Step 5: Health Check Endpoint
```typescript
import Mistral from "@mistralai/mistralai";

export async function GET() {
  try {
    const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });
    await client.models.list();
    return Response.json({ status: "healthy", provider: "mistral" });
  } catch (error) {
    return Response.json({ status: "unhealthy", error: error.message }, { status: 503 });
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key not found | Missing env var | Verify secret configuration on platform |
| Function timeout | Long completion | Increase `maxDuration`, use streaming |
| Cold start latency | Serverless spin-up | Set minimum instances or use edge runtime |
| Model not available | Wrong model ID | Check available models at console.mistral.ai |

## Examples

### Production Client Wrapper
```typescript
const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY!,
  timeout: 60000,
  maxRetries: 3,
});
```

## Resources
- [Mistral AI API Documentation](https://docs.mistral.ai)
- [Mistral AI Models](https://docs.mistral.ai/getting-started/models)

## Next Steps
For multi-environment setup, see `mistral-multi-env-setup`.
