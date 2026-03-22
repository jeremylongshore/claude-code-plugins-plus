---
name: mistral-deploy-integration
description: |
  Deploy Mistral AI integrations to Vercel, Docker, and Cloud Run platforms.
  Use when deploying Mistral AI-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy mistral", "mistral Vercel",
  "mistral production deploy", "mistral Cloud Run", "mistral Docker".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(docker:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, deployment]

---
# Mistral AI Deploy Integration

## Overview
Deploy Mistral AI-powered applications to production with secure API key management. Covers Vercel (Edge + Serverless), Docker, Cloud Run, and self-hosted vLLM deployments. All connect to `api.mistral.ai` or your own inference endpoint.

## Prerequisites
- Mistral AI production API key
- Platform CLI installed (vercel, docker, or gcloud)
- Application using `@mistralai/mistralai` SDK

## Instructions

### Step 1: Platform Secret Configuration

```bash
set -euo pipefail
# Vercel
vercel env add MISTRAL_API_KEY production
vercel env add MISTRAL_MODEL production  # optional: default model

# Cloud Run
echo -n "your-key" | gcloud secrets create mistral-api-key --data-file=-

# Docker
echo "MISTRAL_API_KEY=your-key" > .env.production
echo ".env.production" >> .gitignore
```

### Step 2: Vercel Edge Function

```typescript
// api/chat.ts — Vercel Edge Function with streaming
import { Mistral } from '@mistralai/mistralai';

export const config = { runtime: 'edge' };

export default async function handler(req: Request) {
  const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });
  const { messages, stream = false } = await req.json();

  if (stream) {
    const streamResponse = await client.chat.stream({
      model: process.env.MISTRAL_MODEL ?? 'mistral-small-latest',
      messages,
    });

    const encoder = new TextEncoder();
    const readable = new ReadableStream({
      async start(controller) {
        for await (const event of streamResponse) {
          const content = event.data?.choices?.[0]?.delta?.content;
          if (content) {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content })}\n\n`));
          }
        }
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      },
    });

    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    });
  }

  const response = await client.chat.complete({
    model: process.env.MISTRAL_MODEL ?? 'mistral-small-latest',
    messages,
  });

  return Response.json(response);
}
```

### Step 3: Docker Deployment

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -sf http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

```bash
set -euo pipefail
docker build -t mistral-app .
docker run -d --name mistral-app \
  -p 3000:3000 \
  -e MISTRAL_API_KEY="$MISTRAL_API_KEY" \
  -e MISTRAL_MODEL="mistral-small-latest" \
  mistral-app
```

### Step 4: Cloud Run Deployment

```bash
set -euo pipefail
# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/mistral-app

# Deploy with secret injection
gcloud run deploy mistral-service \
  --image gcr.io/$PROJECT_ID/mistral-app \
  --region us-central1 \
  --platform managed \
  --set-secrets=MISTRAL_API_KEY=mistral-api-key:latest \
  --set-env-vars=MISTRAL_MODEL=mistral-small-latest \
  --min-instances=1 \
  --max-instances=10 \
  --memory=512Mi \
  --timeout=60s
```

### Step 5: Self-Hosted with vLLM

For data sovereignty or latency requirements, self-host open-weight Mistral models:

```bash
set -euo pipefail
# Serve Mistral with vLLM (OpenAI-compatible API)
docker run --runtime nvidia --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  -e HF_TOKEN="$HF_TOKEN" \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-Small-24B-Instruct-2501 \
  --dtype auto \
  --api-key "your-local-key"
```

Point the SDK at your local endpoint:

```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: 'your-local-key',
  serverURL: 'http://localhost:8000', // vLLM endpoint
});
```

### Step 6: Health Check Endpoint

```typescript
import { Mistral } from '@mistralai/mistralai';

export async function GET() {
  const start = performance.now();
  try {
    const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });
    await client.models.list();
    return Response.json({
      status: 'healthy',
      provider: 'mistral',
      latencyMs: Math.round(performance.now() - start),
    });
  } catch (error: any) {
    return Response.json(
      { status: 'unhealthy', error: error.message },
      { status: 503 },
    );
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key not found | Missing env/secret | Verify secret config on platform |
| Function timeout | Long completion | Increase timeout, use streaming |
| Cold start latency | Serverless spin-up | Set `min-instances=1` or use edge |
| vLLM OOM | Model too large for GPU | Use quantized model or smaller variant |

## Resources
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [vLLM Deployment](https://docs.mistral.ai/deployment/self-deployment/vllm/)
- [Cloud Deployment](https://docs.mistral.ai/deployment/ai-studio/)

## Output
- Platform-specific deployment configurations
- Secure API key management per platform
- Streaming support for Edge/Serverless
- Health check endpoint
- Self-hosted option with vLLM
