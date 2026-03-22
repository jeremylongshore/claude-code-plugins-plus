---
name: assemblyai-deploy-integration
description: |
  Deploy AssemblyAI integrations to Vercel, Cloud Run, and Fly.io platforms.
  Use when deploying AssemblyAI-powered transcription services to production,
  configuring platform-specific secrets, or setting up webhook endpoints.
  Trigger with phrases like "deploy assemblyai", "assemblyai Vercel",
  "assemblyai production deploy", "assemblyai Cloud Run", "assemblyai Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, speech-to-text, assemblyai, transcription, deploy]
compatible-with: claude-code
---

# AssemblyAI Deploy Integration

## Overview
Deploy AssemblyAI-powered transcription services to Vercel (serverless), Google Cloud Run (containers), and Fly.io with proper secrets management and webhook configuration.

## Prerequisites
- AssemblyAI API key for production
- Platform CLI installed (`vercel`, `gcloud`, or `fly`)
- Application with working AssemblyAI integration

## Instructions

### Vercel Deployment (Serverless)

```bash
# Add secrets
vercel env add ASSEMBLYAI_API_KEY production
vercel env add ASSEMBLYAI_WEBHOOK_SECRET production

# Deploy
vercel --prod
```

**API Route for Transcription:**
```typescript
// app/api/transcribe/route.ts (Next.js App Router)
import { AssemblyAI } from 'assemblyai';
import { NextRequest, NextResponse } from 'next/server';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export async function POST(req: NextRequest) {
  const { audioUrl, features } = await req.json();

  if (!audioUrl) {
    return NextResponse.json({ error: 'audioUrl required' }, { status: 400 });
  }

  // Use submit() + webhook for production (non-blocking)
  const transcript = await client.transcripts.submit({
    audio: audioUrl,
    webhook_url: `${process.env.NEXT_PUBLIC_APP_URL}/api/webhooks/assemblyai`,
    webhook_auth_header_name: 'X-Webhook-Secret',
    webhook_auth_header_value: process.env.ASSEMBLYAI_WEBHOOK_SECRET!,
    speaker_labels: features?.speakerLabels ?? false,
    sentiment_analysis: features?.sentiment ?? false,
  });

  return NextResponse.json({
    transcriptId: transcript.id,
    status: transcript.status,
  });
}
```

**Webhook Handler:**
```typescript
// app/api/webhooks/assemblyai/route.ts
import { AssemblyAI } from 'assemblyai';
import { NextRequest, NextResponse } from 'next/server';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export async function POST(req: NextRequest) {
  // Verify webhook authenticity
  const secret = req.headers.get('x-webhook-secret');
  if (secret !== process.env.ASSEMBLYAI_WEBHOOK_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { transcript_id, status } = await req.json();

  if (status === 'completed') {
    const transcript = await client.transcripts.get(transcript_id);
    // Store transcript, notify user, trigger downstream processing
    console.log(`Transcript ${transcript_id} completed: ${transcript.text?.length} chars`);
  } else if (status === 'error') {
    console.error(`Transcript ${transcript_id} failed`);
  }

  return NextResponse.json({ received: true });
}
```

**Vercel config:**
```json
{
  "functions": {
    "app/api/transcribe/route.ts": { "maxDuration": 60 },
    "app/api/webhooks/assemblyai/route.ts": { "maxDuration": 10 }
  }
}
```

### Google Cloud Run Deployment

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 8080
CMD ["node", "dist/server.js"]
```

```bash
# Store secret in Secret Manager
echo -n "your-api-key" | gcloud secrets create assemblyai-api-key --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/assemblyai-service

gcloud run deploy assemblyai-service \
  --image gcr.io/$PROJECT_ID/assemblyai-service \
  --region us-central1 \
  --platform managed \
  --set-secrets=ASSEMBLYAI_API_KEY=assemblyai-api-key:latest \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 300
```

### Fly.io Deployment

```toml
# fly.toml
app = "my-assemblyai-app"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  PORT = "3000"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
```

```bash
fly secrets set ASSEMBLYAI_API_KEY=your-api-key
fly secrets set ASSEMBLYAI_WEBHOOK_SECRET=your-webhook-secret
fly deploy
```

### Streaming Token Endpoint (All Platforms)

```typescript
// Endpoint to generate temporary tokens for browser streaming
// Works on any platform — the key is to never expose your API key to the client

import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export async function GET() {
  const token = await client.streaming.createTemporaryToken({
    expires_in_seconds: 300,
  });

  return Response.json({ token });
}
```

### Health Check (Platform-Agnostic)

```typescript
import { AssemblyAI } from 'assemblyai';

const client = new AssemblyAI({
  apiKey: process.env.ASSEMBLYAI_API_KEY!,
});

export async function GET() {
  const start = Date.now();
  try {
    await client.transcripts.list({ limit: 1 });
    return Response.json({
      status: 'healthy',
      assemblyai: { connected: true, latencyMs: Date.now() - start },
      timestamp: new Date().toISOString(),
    });
  } catch {
    return Response.json({
      status: 'degraded',
      assemblyai: { connected: false, latencyMs: Date.now() - start },
      timestamp: new Date().toISOString(),
    }, { status: 503 });
  }
}
```

## Output
- Application deployed with AssemblyAI secrets securely configured
- Webhook endpoint for async transcription notifications
- Streaming token endpoint for browser clients
- Health check endpoint monitoring AssemblyAI connectivity

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not available at runtime | Wrong env name or missing secret | Verify with platform CLI |
| Webhook not receiving events | URL not publicly accessible | Verify URL, check firewall/CORS |
| Function timeout (Vercel) | `transcribe()` takes too long | Use `submit()` + webhook pattern |
| Cold start latency | Serverless spin-up | Set minimum instances or use `submit()` |

## Resources
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Fly.io Secrets](https://fly.io/docs/reference/secrets/)
- [AssemblyAI Webhooks](https://www.assemblyai.com/docs/getting-started/webhooks)

## Next Steps
For webhook handling, see `assemblyai-webhooks-events`.
