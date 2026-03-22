---
name: elevenlabs-deploy-integration
description: |
  Deploy ElevenLabs TTS applications to Vercel, Fly.io, and Cloud Run.
  Use when deploying ElevenLabs-powered apps to production,
  configuring platform-specific secrets, or setting up serverless TTS.
  Trigger: "deploy elevenlabs", "elevenlabs Vercel", "elevenlabs Cloud Run",
  "elevenlabs Fly.io", "elevenlabs serverless", "host TTS API".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, ai, elevenlabs, deployment, serverless]
compatible-with: claude-code
---

# ElevenLabs Deploy Integration

## Overview

Deploy ElevenLabs TTS/voice applications to cloud platforms. Covers Vercel (serverless), Fly.io (containers), and Google Cloud Run with proper secrets management, timeout configuration, and streaming support.

## Prerequisites

- ElevenLabs API key for production
- Platform CLI installed (`vercel`, `fly`, or `gcloud`)
- Application code tested locally

## Instructions

### Vercel Deployment (Serverless)

**Key constraint:** Vercel functions have a 10-second timeout on Hobby (30s on Pro). Use Flash model for speed.

```bash
# Set secrets
vercel env add ELEVENLABS_API_KEY production
vercel env add ELEVENLABS_API_KEY preview

# Deploy
vercel --prod
```

**API Route (Next.js / Vercel):**
```typescript
// app/api/tts/route.ts
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 30; // Vercel Pro max

const client = new ElevenLabsClient();

export async function POST(req: Request) {
  const { text, voiceId = "21m00Tcm4TlvDq8ikWAM" } = await req.json();

  if (!text || text.length > 5000) {
    return NextResponse.json(
      { error: "Text required, max 5000 characters" },
      { status: 400 }
    );
  }

  try {
    const audio = await client.textToSpeech.convert(voiceId, {
      text,
      model_id: "eleven_flash_v2_5",  // Fast for serverless
      output_format: "mp3_22050_32",
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.75,
      },
    });

    return new Response(audio as any, {
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "public, max-age=3600",
      },
    });
  } catch (error: any) {
    const status = error.statusCode || 500;
    return NextResponse.json(
      { error: error.message || "TTS generation failed" },
      { status }
    );
  }
}
```

**vercel.json:**
```json
{
  "env": {
    "ELEVENLABS_API_KEY": "@elevenlabs_api_key"
  },
  "functions": {
    "app/api/tts/route.ts": {
      "maxDuration": 30
    }
  }
}
```

### Fly.io Deployment (Container)

Better for long-running TTS, WebSocket streaming, and high concurrency.

**fly.toml:**
```toml
app = "my-tts-service"
primary_region = "iad"

[env]
  NODE_ENV = "production"
  # Use the closest region to ElevenLabs servers (US East)
  ELEVENLABS_MODEL = "eleven_multilingual_v2"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

```bash
# Set secrets
fly secrets set ELEVENLABS_API_KEY=sk_your_prod_key
fly secrets set ELEVENLABS_WEBHOOK_SECRET=whsec_your_secret

# Deploy
fly deploy

# Check logs
fly logs
```

**Express server with streaming:**
```typescript
// server.ts
import express from "express";
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { Readable } from "stream";

const app = express();
app.use(express.json());

const client = new ElevenLabsClient();

// Streaming TTS endpoint
app.post("/api/tts/stream", async (req, res) => {
  const { text, voiceId = "21m00Tcm4TlvDq8ikWAM", modelId } = req.body;

  res.setHeader("Content-Type", "audio/mpeg");
  res.setHeader("Transfer-Encoding", "chunked");

  try {
    const stream = await client.textToSpeech.stream(voiceId, {
      text,
      model_id: modelId || "eleven_flash_v2_5",
      output_format: "mp3_22050_32",
    });

    // Pipe streaming audio directly to response
    const readable = Readable.fromWeb(stream as any);
    readable.pipe(res);
  } catch (error: any) {
    if (!res.headersSent) {
      res.status(error.statusCode || 500).json({ error: error.message });
    }
  }
});

// Health check
app.get("/health", async (_req, res) => {
  try {
    const user = await client.user.get();
    res.json({
      status: "healthy",
      quota: {
        used: user.subscription.character_count,
        limit: user.subscription.character_limit,
      },
    });
  } catch {
    res.status(503).json({ status: "unhealthy" });
  }
});

app.listen(3000, () => console.log("TTS service running on :3000"));
```

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy tts-service \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets=ELEVENLABS_API_KEY=elevenlabs-api-key:latest \
  --timeout=60 \
  --concurrency=10 \
  --min-instances=0 \
  --max-instances=5

# Store secret in Secret Manager first
echo -n "sk_your_prod_key" | gcloud secrets create elevenlabs-api-key --data-file=-
```

**Dockerfile:**
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

## Platform Comparison for ElevenLabs

| Feature | Vercel | Fly.io | Cloud Run |
|---------|--------|--------|-----------|
| Max timeout | 30s (Pro) | No limit | 60min |
| WebSocket streaming | Limited | Full support | Full support |
| Cold start | ~1-3s | ~0.5-2s | ~1-5s |
| Concurrency | Per-function | Per-VM | Per-instance |
| Best for | Simple TTS API | Streaming/WebSocket | Variable load |
| Min cost | Free tier | ~$2/mo | Free tier |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Vercel timeout | TTS > 10s on Hobby | Upgrade to Pro (30s) or use Flash model |
| Cold start slow | Container initialization | Set `min_instances=1` (Cloud Run) or `min_machines=1` (Fly) |
| Secret not found | Missing platform config | Add via platform CLI |
| Streaming broken | Proxy buffering | Disable response buffering in nginx/CDN |
| CORS errors | Missing headers | Add `Access-Control-Allow-Origin` to TTS endpoint |

## Resources

- [Vercel Functions](https://vercel.com/docs/functions)
- [Fly.io Node.js](https://fly.io/docs/languages-and-frameworks/node/)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [ElevenLabs API Quickstart](https://elevenlabs.io/docs/eleven-api/quickstart)

## Next Steps

For webhook handling, see `elevenlabs-webhooks-events`.
