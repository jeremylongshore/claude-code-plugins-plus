---
name: fireflies-deploy-integration
description: |
  Deploy Fireflies.ai webhook receivers and GraphQL clients to Vercel, Docker, and Cloud Run.
  Use when deploying Fireflies.ai-powered applications to production,
  configuring platform-specific secrets, or hosting webhook endpoints.
  Trigger with phrases like "deploy fireflies", "fireflies Vercel",
  "fireflies production deploy", "fireflies Cloud Run", "fireflies Docker".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(docker:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, deployment]

---
# Fireflies.ai Deploy Integration

## Overview
Deploy Fireflies.ai integrations across platforms. Covers GraphQL client setup, webhook receiver deployment, and secret management for Vercel, Docker, and Google Cloud Run.

## Prerequisites
- Fireflies.ai Business+ plan for API access
- `FIREFLIES_API_KEY` and `FIREFLIES_WEBHOOK_SECRET` ready
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Shared GraphQL Client
```typescript
// lib/fireflies.ts
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

export async function firefliesQuery(query: string, variables?: any) {
  const res = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  const json = await res.json();
  if (json.errors) throw new Error(json.errors[0].message);
  return json.data;
}
```

### Step 2: Webhook Receiver (Next.js / Vercel)
```typescript
// app/api/webhooks/fireflies/route.ts
import crypto from "crypto";

export async function POST(req: Request) {
  const rawBody = await req.text();
  const signature = req.headers.get("x-hub-signature") || "";

  // Verify HMAC-SHA256 signature
  const expected = crypto
    .createHmac("sha256", process.env.FIREFLIES_WEBHOOK_SECRET!)
    .update(rawBody)
    .digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return Response.json({ error: "Invalid signature" }, { status: 401 });
  }

  const event = JSON.parse(rawBody);

  if (event.eventType === "Transcription completed") {
    // Fetch transcript data
    const data = await firefliesQuery(`
      query($id: String!) {
        transcript(id: $id) {
          id title duration
          speakers { name }
          summary { overview action_items }
        }
      }
    `, { id: event.meetingId });

    // Process transcript (store, notify, create tasks)
    console.log(`Processed: ${data.transcript.title}`);
  }

  return Response.json({ received: true });
}
```

### Step 3: Deploy to Vercel
```bash
set -euo pipefail
# Add secrets
vercel env add FIREFLIES_API_KEY production
vercel env add FIREFLIES_WEBHOOK_SECRET production

# Deploy
vercel --prod

# Register webhook URL in Fireflies dashboard:
# https://your-app.vercel.app/api/webhooks/fireflies
```

### Step 4: Deploy with Docker
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```yaml
# docker-compose.yml
services:
  fireflies-app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - FIREFLIES_API_KEY=${FIREFLIES_API_KEY}
      - FIREFLIES_WEBHOOK_SECRET=${FIREFLIES_WEBHOOK_SECRET}
    restart: unless-stopped
```

```bash
set -euo pipefail
docker compose up -d
# Verify
curl -f http://localhost:3000/api/health | jq .
```

### Step 5: Deploy to Google Cloud Run
```bash
set -euo pipefail
# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/fireflies-app

# Deploy
gcloud run deploy fireflies-app \
  --image gcr.io/$PROJECT_ID/fireflies-app \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "FIREFLIES_WEBHOOK_SECRET=${FIREFLIES_WEBHOOK_SECRET}" \
  --set-secrets "FIREFLIES_API_KEY=fireflies-api-key:latest"

# Get URL for webhook registration
gcloud run services describe fireflies-app --format='value(status.url)'
```

### Step 6: Health Check Endpoint
```typescript
// app/api/health/route.ts (or /health endpoint)
export async function GET() {
  try {
    const start = Date.now();
    const data = await firefliesQuery("{ user { email } }");
    return Response.json({
      status: "healthy",
      fireflies: {
        connected: true,
        user: data.user.email,
        latencyMs: Date.now() - start,
      },
    });
  } catch (err) {
    return Response.json({
      status: "degraded",
      fireflies: { connected: false, error: (err as Error).message },
    }, { status: 503 });
  }
}
```

## Post-Deploy: Register Webhook
After deploying, register your webhook URL:
1. Go to [app.fireflies.ai/settings](https://app.fireflies.ai/settings) > Developer settings
2. Enter your webhook URL (e.g., `https://your-app.vercel.app/api/webhooks/fireflies`)
3. Save the webhook secret

Or test via API:
```bash
set -euo pipefail
# Test API connectivity from deployed app
curl -f https://your-app.vercel.app/api/health | jq .
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| GraphQL auth error | API key not set in platform | Add secret via platform CLI |
| Webhook 401 | Secret mismatch | Verify secret matches dashboard |
| Cold start timeout | Serverless cold start + API latency | Increase function timeout to 30s |
| No webhook events | URL not registered | Register at app.fireflies.ai/settings |

## Output
- Deployed webhook receiver with HMAC signature verification
- GraphQL client configured with platform-specific secrets
- Health check endpoint monitoring Fireflies connectivity
- Platform-specific deployment verified

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Fireflies Webhooks](https://docs.fireflies.ai/graphql-api/webhooks)

## Next Steps
For webhook event handling, see `fireflies-webhooks-events`.
