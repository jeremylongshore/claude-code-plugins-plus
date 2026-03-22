---
name: cohere-deploy-integration
description: |
  Deploy Cohere-powered applications to Vercel, Fly.io, and Cloud Run.
  Use when deploying Cohere API v2 apps to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy cohere", "cohere Vercel",
  "cohere production deploy", "cohere Cloud Run", "cohere Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Deploy Integration

## Overview
Deploy Cohere API v2 applications to Vercel, Fly.io, and Google Cloud Run with proper secrets management and health checks.

## Prerequisites
- Cohere production API key (not trial)
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)
- Application tested locally with real API calls

## Instructions

### Vercel Deployment

```bash
# Add Cohere API key as Vercel environment variable
vercel env add CO_API_KEY production
# Paste your production key when prompted

# Deploy
vercel --prod
```

**vercel.json:**
```json
{
  "env": {
    "CO_API_KEY": "@co_api_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

**Vercel API Route (streaming chat):**
```typescript
// api/chat/route.ts
import { CohereClientV2 } from 'cohere-ai';

const cohere = new CohereClientV2();

export async function POST(req: Request) {
  const { message } = await req.json();

  const stream = await cohere.chatStream({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: message }],
  });

  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      for await (const event of stream) {
        if (event.type === 'content-delta') {
          const text = event.delta?.message?.content?.text ?? '';
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
        }
      }
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });

  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
  });
}
```

### Fly.io Deployment

```bash
# Set Cohere API key
fly secrets set CO_API_KEY="your-production-key"

# Deploy
fly deploy
```

**fly.toml:**
```toml
app = "my-cohere-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[services.http_checks]]
  interval = 30000
  timeout = 5000
  path = "/api/health"
```

### Google Cloud Run Deployment

```bash
#!/bin/bash
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
SERVICE="cohere-app"
REGION="us-central1"

# Store key in Secret Manager
echo -n "$CO_API_KEY" | gcloud secrets create cohere-api-key --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE

gcloud run deploy $SERVICE \
  --image gcr.io/$PROJECT_ID/$SERVICE \
  --region $REGION \
  --platform managed \
  --set-secrets=CO_API_KEY=cohere-api-key:latest \
  --max-instances 10 \
  --min-instances 1 \
  --timeout 30
```

**Dockerfile:**
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
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Health Check (All Platforms)

```typescript
// api/health.ts — works on Vercel, Fly, Cloud Run
import { CohereClientV2, CohereError } from 'cohere-ai';

export async function GET() {
  const start = Date.now();
  let status: 'healthy' | 'degraded' | 'down';

  try {
    const cohere = new CohereClientV2();
    await cohere.chat({
      model: 'command-r7b-12-2024',
      messages: [{ role: 'user', content: 'ping' }],
      maxTokens: 1,
    });
    status = 'healthy';
  } catch (err) {
    status = err instanceof CohereError && err.statusCode === 429
      ? 'degraded'
      : 'down';
  }

  return Response.json({
    status,
    cohere: { latencyMs: Date.now() - start },
    timestamp: new Date().toISOString(),
  });
}
```

### Environment Configuration

```typescript
// config/cohere.ts
interface CohereConfig {
  model: string;
  maxTokens: number;
  timeout: number;
}

const configs: Record<string, CohereConfig> = {
  development: {
    model: 'command-r7b-12-2024', // cheap for dev
    maxTokens: 500,
    timeout: 30,
  },
  production: {
    model: 'command-a-03-2025',   // best for prod
    maxTokens: 4096,
    timeout: 60,
  },
};

export function getCohereConfig(): CohereConfig {
  const env = process.env.NODE_ENV ?? 'development';
  return configs[env] ?? configs.development;
}
```

## Output
- Application deployed with Cohere API key in platform secret store
- Health check endpoint verifying Cohere connectivity
- Streaming chat endpoint for user-facing applications
- Environment-specific model selection

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 401 after deploy | Wrong key env var name | Verify `CO_API_KEY` is set |
| Timeout on Vercel | Default 10s limit | Set `maxDuration: 30` in vercel.json |
| Cold start latency | Serverless spin-up | Set `min-instances: 1` (Cloud Run/Fly) |
| Stream breaks | Platform timeout | Use chunked transfer encoding |

## Resources
- [Cohere Going Live](https://docs.cohere.com/docs/going-live)
- [Vercel Functions](https://vercel.com/docs/functions)
- [Fly.io App Configuration](https://fly.io/docs/reference/configuration/)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)

## Next Steps
For structured output and connectors, see `cohere-webhooks-events`.
