---
name: ideogram-deploy-integration
description: |
  Deploy Ideogram integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Ideogram-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy ideogram", "ideogram Vercel",
  "ideogram production deploy", "ideogram Cloud Run", "ideogram Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Ideogram Deploy Integration

## Overview
Deploy applications using Ideogram's AI image generation API (`api.ideogram.ai`). Covers API key management, deploying generation endpoints with proper timeout configuration, image storage setup, and CDN integration for serving generated images.

## Prerequisites
- Ideogram API key stored in `IDEOGRAM_API_KEY` environment variable
- Cloud storage for generated images (S3, GCS, or R2)
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel
vercel env add IDEOGRAM_API_KEY production
vercel env add IMAGE_STORAGE_BUCKET production

# Cloud Run
echo -n "your-key" | gcloud secrets create ideogram-api-key --data-file=-
```

### Step 2: Generation API Endpoint
```typescript
// api/generate.ts
export async function POST(req: Request) {
  const { prompt, style, aspectRatio } = await req.json();

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
        style_type: style || "REALISTIC",
        aspect_ratio: aspectRatio || "ASPECT_1_1",
        magic_prompt_option: "AUTO",
      },
    }),
  });

  const result = await response.json();

  // Upload to cloud storage
  const images = [];
  for (const img of result.data) {
    const stored = await uploadToStorage(img.url);
    images.push(stored);
  }

  return Response.json({ images });
}
```

### Step 3: Docker with Image Processing
```dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y libvips-dev
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Step 4: Vercel Configuration
```json
{
  "functions": {
    "api/generate.ts": {
      "maxDuration": 60
    }
  }
}
```

### Step 5: Health Check
```typescript
export async function GET() {
  const hasKey = !!process.env.IDEOGRAM_API_KEY;
  return Response.json({ status: hasKey ? "healthy" : "missing_key" });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Generation timeout | Complex prompt | Increase function timeout to 60s |
| Content filtered | Prompt policy violation | Review Ideogram content guidelines |
| Storage upload fails | Bad credentials | Verify storage bucket permissions |
| Rate limited | Too many requests | Queue generation jobs |

## Examples

### Quick Deploy
```bash
vercel env add IDEOGRAM_API_KEY production && vercel --prod
```

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [Ideogram Models](https://developer.ideogram.ai/models)

## Next Steps
For multi-environment setup, see `ideogram-multi-env-setup`.
