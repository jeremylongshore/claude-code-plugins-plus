---
name: anthropic-deploy-integration
description: |
  Deploy Anthropic integrations to production platforms.
  Use when deploying Anthropic-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy anthropic", "anthropic production",
  "anthropic production deploy", "anthropic CI/CD".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic]
---

# Anthropic Deploy Integration

## Overview

Deploy Anthropic-powered applications as stateless API wrappers — serverless functions
that receive user requests, call the Anthropic model API, and stream responses back.


## Prerequisites
- Anthropic API keys for production environment
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
import { Client } from '@anthropic/sdk';

export const config = { runtime: 'edge' };

export default async function handler(req: Request) {
  const client = new Client({ apiKey: process.env.ANTHROPIC_API_KEY });
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
vercel secrets add anthropic_api_key "$ANTHROPIC_API_KEY"
vercel --prod
```


## Health Check Endpoint

```typescript
// api/health.ts
export async function GET() {
  const anthropicStatus = await checkAnthropicConnection();

  return Response.json({
    status: anthropicStatus ? 'healthy' : 'degraded',
    services: {
      anthropic: anthropicStatus,
    },
    timestamp: new Date().toISOString(),
  });
}
```

## Instructions

### Step 1: Choose Deployment Platform
Select the platform that best fits your infrastructure needs and follow the platform-specific guide above.

### Step 2: Configure Secrets
Store Anthropic API keys securely using the platform's secrets management.

### Step 3: Deploy Application
Use the platform CLI to deploy your application with Anthropic integration.

### Step 4: Verify Health
Test the health check endpoint to confirm Anthropic connectivity.

## Output
- Application deployed to production
- Anthropic secrets securely configured
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
- [Anthropic Deploy Guide](https://docs.anthropic.com/deploy)

## Next Steps
For webhook handling, see `anthropic-webhooks-events`.