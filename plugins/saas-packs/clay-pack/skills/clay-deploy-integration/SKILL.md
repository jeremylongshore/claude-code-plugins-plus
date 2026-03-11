---
name: clay-deploy-integration
description: |
  Deploy Clay integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Clay-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy clay", "clay Vercel",
  "clay production deploy", "clay Cloud Run", "clay Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Deploy Integration

## Overview
Deploy applications that integrate with Clay's data enrichment API to production. Covers setting up API credentials, configuring webhook endpoints for enrichment callbacks, and deploying to Vercel, Docker, or Cloud Run with proper secrets management for Clay API access.

## Prerequisites
- Clay API key stored securely
- Application using Clay REST API for enrichment
- Platform CLI installed (vercel, docker, or gcloud)
- Webhook endpoint for enrichment callbacks

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel
vercel env add CLAY_API_KEY production
vercel env add CLAY_WEBHOOK_SECRET production

# Docker
echo "CLAY_API_KEY=your-key" >> .env.production

# Cloud Run
echo -n "your-key" | gcloud secrets create clay-api-key --data-file=-
```

### Step 2: Application Configuration
```typescript
// config/clay.ts
export function getClayConfig() {
  return {
    apiKey: process.env.CLAY_API_KEY!,
    baseUrl: "https://api.clay.com/v1",
    webhookSecret: process.env.CLAY_WEBHOOK_SECRET!,
    webhookUrl: process.env.CLAY_WEBHOOK_URL || "https://api.yourapp.com/webhooks/clay",
  };
}
```

### Step 3: Docker Deployment
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

```bash
set -euo pipefail
docker build -t clay-integration .
docker run -d \
  -e CLAY_API_KEY="$CLAY_API_KEY" \
  -e CLAY_WEBHOOK_SECRET="$CLAY_WEBHOOK_SECRET" \
  -p 3000:3000 clay-integration  # 3000: 3 seconds in ms
```

### Step 4: Vercel Deployment
```bash
vercel env add CLAY_API_KEY production
vercel --prod
```

### Step 5: Health Check
```typescript
export async function GET() {
  try {
    const response = await fetch("https://api.clay.com/v1/tables", {
      headers: { "Authorization": `Bearer ${process.env.CLAY_API_KEY}` },
    });
    return Response.json({ status: response.ok ? "healthy" : "degraded" });
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });  # HTTP 503 Service Unavailable
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key rejected | Key invalid or expired | Regenerate key in Clay dashboard |
| Webhook not received | URL not accessible | Verify HTTPS endpoint is public |
| Rate limited | Too many enrichment calls | Implement request queuing |
| Missing enrichment data | Table not configured | Verify table ID and column setup |

## Examples


**Basic usage**: Apply clay deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay deploy integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [Clay API Documentation](https://docs.clay.com/api)
- [Clay Enrichment Guide](https://docs.clay.com/enrichment)

## Next Steps
For webhook handling, see `clay-webhooks-events`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale