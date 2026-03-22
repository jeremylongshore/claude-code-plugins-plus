---
name: langfuse-deploy-integration
description: |
  Deploy Langfuse integrations to production platforms.
  Use when deploying Langfuse-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy langfuse", "langfuse production",
  "langfuse production deploy", "langfuse CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, langfuse]
---

# Langfuse Deploy Integration

## Overview

Deploy Langfuse-powered applications as stateless API wrappers — serverless functions
that receive user requests, call the Langfuse model API, and stream responses back.


## Prerequisites
- Langfuse API keys for production environment
- Platform CLI installed (vercel, fly, or gcloud)
- Application code ready for deployment
- Environment variables documented


## Serverless API Wrapper (Recommended for AI/ML)

### Why Serverless?
AI/ML integrations are stateless request/response — perfect for serverless. Each function
call receives a prompt, calls the model, and returns the response. No connection pools needed.

### Vercel Edge Function
```typescript
// api/chat.ts — streams AI responses at the edge
import { Client } from '@langfuse/sdk';

export const config = { runtime: 'edge' };

export default async function handler(req: Request) {
  const client = new Client({ apiKey: process.env.LANGFUSE_API_KEY });
  const { messages } = await req.json();

  const stream = await client.chat.completions.create({
    model: 'default',
    messages,
    stream: true,
  });

  return new Response(stream.toReadableStream(), {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}
```

### Deploy
```bash
vercel secrets add langfuse_api_key "$LANGFUSE_API_KEY"
vercel --prod
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const langfuseStatus = await checkLangfuseConnection();

  return Response.json({
    status: langfuseStatus ? 'healthy' : 'degraded',
    services: {
      langfuse: langfuseStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Langfuse API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Langfuse integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Langfuse connectivity.

## Output
- Application deployed to production
- Langfuse secrets securely configured
- Health check endpoint functional
- Environment-specific configuration in place

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | Missing configuration | Add secret via platform CLI |
| Deploy timeout | Large build | Increase build timeout |
| Health check fails | Wrong API key | Verify environment variable |
| Cold start issues | No warm-up | Configure minimum instances |

## Resources
- [Vercel Documentation](https://vercel.com/docs)
- [Fly.io Documentation](https://fly.io/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Langfuse Deploy Guide](https://docs.langfuse.com/deploy)

## Next Steps
For webhook handling, see `langfuse-webhooks-events`.