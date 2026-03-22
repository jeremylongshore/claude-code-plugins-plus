---
name: ideogram-deploy-integration
description: |
  Deploy Ideogram integrations to Vercel, Cloud Run, and Docker platforms.
  Use when deploying Ideogram-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy ideogram", "ideogram Vercel",
  "ideogram production deploy", "ideogram Cloud Run", "ideogram Docker".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(gcloud:*), Bash(docker:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, deployment]

---
# Ideogram Deploy Integration

## Overview
Deploy Ideogram image generation endpoints to Vercel, Cloud Run, or Docker. Key concerns: API key security, function timeouts (generation takes 5-15s), image persistence (URLs expire), and CDN integration for serving generated images.

## Prerequisites
- `IDEOGRAM_API_KEY` configured
- Cloud storage for generated images (S3, GCS, or R2)
- Platform CLI installed (vercel, gcloud, or docker)

## Instructions

### Step 1: API Endpoint (Next.js / Vercel)
```typescript
// app/api/generate/route.ts
import { NextRequest, NextResponse } from "next/server";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: process.env.AWS_REGION });

export async function POST(req: NextRequest) {
  const { prompt, style, aspectRatio } = await req.json();

  if (!prompt || prompt.length > 10000) {
    return NextResponse.json({ error: "Invalid prompt" }, { status: 400 });
  }

  // Generate image via Ideogram
  const response = await fetch("https://api.ideogram.ai/generate", {
    method: "POST",
    headers: {
      "Api-Key": process.env.IDEOGRAM_API_KEY!,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_request: {
        prompt,
        model: "V_2",
        style_type: style || "AUTO",
        aspect_ratio: aspectRatio || "ASPECT_1_1",
        magic_prompt_option: "AUTO",
      },
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    return NextResponse.json({ error: `Generation failed: ${response.status}` }, { status: 502 });
  }

  const result = await response.json();
  const image = result.data[0];

  // Download and persist to S3 (Ideogram URLs expire)
  const imgResponse = await fetch(image.url);
  const buffer = Buffer.from(await imgResponse.arrayBuffer());
  const key = `generated/${image.seed}-${Date.now()}.png`;

  await s3.send(new PutObjectCommand({
    Bucket: process.env.S3_BUCKET!,
    Key: key,
    Body: buffer,
    ContentType: "image/png",
  }));

  return NextResponse.json({
    url: `https://${process.env.CDN_DOMAIN}/${key}`,
    seed: image.seed,
    resolution: image.resolution,
    style: image.style_type,
  });
}

export const maxDuration = 60; // Vercel function timeout
```

### Step 2: Vercel Configuration
```json
{
  "functions": {
    "app/api/generate/route.ts": {
      "maxDuration": 60
    }
  },
  "env": {
    "IDEOGRAM_API_KEY": "@ideogram-api-key"
  }
}
```

```bash
set -euo pipefail
# Set secrets
vercel env add IDEOGRAM_API_KEY production
vercel env add S3_BUCKET production
vercel env add CDN_DOMAIN production
```

### Step 3: Cloud Run Deployment
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
# Cloud Run sets PORT automatically
CMD ["node", "dist/server.js"]
```

```bash
set -euo pipefail
# Store API key in Secret Manager
echo -n "$IDEOGRAM_API_KEY" | gcloud secrets create ideogram-api-key --data-file=-

# Deploy with secret mount
gcloud run deploy ideogram-service \
  --image=gcr.io/$PROJECT_ID/ideogram-service \
  --set-secrets=IDEOGRAM_API_KEY=ideogram-api-key:latest \
  --timeout=120 \
  --memory=512Mi \
  --max-instances=10 \
  --allow-unauthenticated
```

### Step 4: Docker Compose (Self-Hosted)
```yaml
# docker-compose.yml
services:
  ideogram-api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - IDEOGRAM_API_KEY=${IDEOGRAM_API_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - NODE_ENV=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

### Step 5: Health Check Endpoint
```typescript
// app/api/health/route.ts
export async function GET() {
  const checks = {
    ideogram: {
      configured: !!process.env.IDEOGRAM_API_KEY,
      keyLength: process.env.IDEOGRAM_API_KEY?.length ?? 0,
    },
    storage: {
      configured: !!process.env.S3_BUCKET,
    },
  };

  const healthy = checks.ideogram.configured && checks.storage.configured;

  return Response.json({
    status: healthy ? "healthy" : "degraded",
    checks,
  }, { status: healthy ? 200 : 503 });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Function timeout | Generation takes 5-15s | Set timeout to 60s+ |
| Content filtered | Prompt policy violation | Return 422 with user-friendly message |
| Storage upload fails | Bad credentials | Verify S3/GCS permissions |
| Rate limited | Too many concurrent users | Queue generation jobs with BullMQ |
| Expired URL | Late download | Download immediately in same request |

## Output
- Deployed API endpoint with image generation
- Images persisted to durable storage with CDN URLs
- Health check endpoint for monitoring
- Platform-specific configuration files

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [Vercel Functions](https://vercel.com/docs/functions)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

## Next Steps
For event-driven patterns, see `ideogram-webhooks-events`.
