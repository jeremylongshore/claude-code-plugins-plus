---
name: instantly-deploy-integration
description: |
  Deploy Instantly integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Instantly-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy instantly", "instantly Vercel",
  "instantly production deploy", "instantly Cloud Run", "instantly Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Deploy Integration

## Overview
Deploy applications integrating with Instantly's email outreach API. Covers deploying webhook receivers for email engagement events, campaign management endpoints, and CRM sync services with proper API credential management.

## Prerequisites
- Instantly API key stored in `INSTANTLY_API_KEY` environment variable
- Application with webhook endpoint for email events
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel
vercel env add INSTANTLY_API_KEY production
vercel env add INSTANTLY_WEBHOOK_SECRET production

# Docker
echo "INSTANTLY_API_KEY=your-key" >> .env.production
```

### Step 2: Deploy Campaign Management API
```typescript
// api/campaigns.ts
export async function GET() {
  const response = await fetch("https://api.instantly.ai/api/v1/campaigns", {
    headers: { "Authorization": `Bearer ${process.env.INSTANTLY_API_KEY}` },
  });
  return Response.json(await response.json());
}

export async function POST(req: Request) {
  const { name, sendingAccounts, schedule } = await req.json();

  const response = await fetch("https://api.instantly.ai/api/v1/campaigns", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.INSTANTLY_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, sending_accounts: sendingAccounts, schedule }),
  });

  return Response.json(await response.json());
}
```

### Step 3: Webhook Receiver Deployment
```typescript
// api/webhooks/instantly.ts
export async function POST(req: Request) {
  const apiKey = req.headers.get("x-api-key");
  if (apiKey !== process.env.INSTANTLY_WEBHOOK_SECRET) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });  # HTTP 401 Unauthorized
  }

  const { event_type, data } = await req.json();

  switch (event_type) {
    case "email.replied":
      await syncReplyToCRM(data);
      break;
    case "email.bounced":
      await handleBounce(data);
      break;
  }

  return Response.json({ received: true });
}
```

### Step 4: Docker Deployment
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

### Step 5: Health Check
```typescript
export async function GET() {
  try {
    const response = await fetch("https://api.instantly.ai/api/v1/campaigns?limit=1", {
      headers: { "Authorization": `Bearer ${process.env.INSTANTLY_API_KEY}` },
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
| API auth failure | Invalid key | Regenerate in Instantly dashboard |
| Webhook not received | URL unreachable | Verify HTTPS endpoint accessibility |
| Campaign not sending | Account warming | Check sending account warmup status |
| Rate limited | Too many API calls | Implement request throttling |

## Examples


**Basic usage**: Apply instantly deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize instantly deploy integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [Instantly API Documentation](https://developer.instantly.ai)
- [Instantly Campaign Guide](https://developer.instantly.ai/campaigns)

## Next Steps
For webhook handling, see `instantly-webhooks-events`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale