---
name: lindy-deploy-integration
description: |
  Deploy applications that integrate with Lindy AI agents.
  Use when deploying webhook receivers, callback handlers,
  or applications connected to Lindy agents.
  Trigger with phrases like "deploy lindy", "lindy deployment",
  "lindy production deploy", "release lindy integration".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(docker:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, deployment]

---
# Lindy Deploy Integration

## Overview
Lindy agents run on Lindy's managed infrastructure. Deployment focuses on your
**integration layer**: webhook receivers, callback handlers, and application code
that Lindy agents interact with via HTTP Request actions and webhook triggers.

## Prerequisites
- Lindy agents configured and tested
- Application with webhook receiver endpoints
- Deployment platform (Vercel, Railway, Docker, AWS, GCP)
- Lindy API key and webhook secrets

## Instructions

### Step 1: Prepare Application for Deployment
```typescript
// src/server.ts — Production-ready Lindy webhook receiver
import express from 'express';
import helmet from 'helmet';

const app = express();
app.use(helmet());
app.use(express.json({ limit: '1mb' }));

// Health check for load balancer
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: process.env.APP_VERSION || 'unknown',
  });
});

// Lindy webhook receiver with auth verification
app.post('/lindy/callback', (req, res) => {
  const auth = req.headers.authorization;
  if (auth !== `Bearer ${process.env.LINDY_WEBHOOK_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Respond immediately, process async
  res.json({ received: true });

  // Async processing
  processWebhook(req.body).catch(err => {
    console.error('Webhook processing error:', err);
  });
});

async function processWebhook(payload: any) {
  const { taskId, status, result } = payload;
  // Your business logic here
  console.log(`Task ${taskId}: ${status}`, result);
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Listening on :${PORT}`));
```

### Step 2: Docker Deployment
```dockerfile
# Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY dist/ ./dist/
EXPOSE 3000
ENV NODE_ENV=production
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

```bash
# Build and run
docker build -t lindy-integration .
docker run -d \
  -p 3000:3000 \
  -e LINDY_API_KEY="$LINDY_API_KEY" \
  -e LINDY_WEBHOOK_SECRET="$LINDY_WEBHOOK_SECRET" \
  --name lindy-app \
  lindy-integration
```

### Step 3: Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Set secrets
vercel secrets add lindy-api-key "$LINDY_API_KEY"
vercel secrets add lindy-webhook-secret "$LINDY_WEBHOOK_SECRET"

# Deploy
vercel --prod
```

```json
// vercel.json
{
  "env": {
    "LINDY_API_KEY": "@lindy-api-key",
    "LINDY_WEBHOOK_SECRET": "@lindy-webhook-secret"
  }
}
```

### Step 4: Update Lindy Agent Webhook URLs
After deployment, update all Lindy agents with production URLs:

1. In Lindy dashboard, open each agent with a webhook trigger
2. Navigate to the **HTTP Request** action (if agent calls your API)
3. Update URL from dev/staging to production:
   ```
   OLD: https://abc123.ngrok.io/lindy/callback
   NEW: https://api.yourapp.com/lindy/callback
   ```
4. For webhook triggers, callers need the Lindy-generated URL (unchanged)
5. Test with a sample webhook to verify end-to-end

### Step 5: Post-Deploy Verification
```bash
#!/bin/bash
echo "=== Post-Deploy Verification ==="

PROD_URL="https://api.yourapp.com"

# Health check
echo "[1/3] Health check..."
curl -sf "$PROD_URL/health" | jq .

# Webhook endpoint reachable
echo "[2/3] Webhook endpoint..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$PROD_URL/lindy/callback" \
  -H "Authorization: Bearer $LINDY_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"test": true}')
echo "Webhook endpoint: HTTP $STATUS (expect 200)"

# Trigger a test agent run
echo "[3/3] Agent trigger test..."
curl -s -X POST "https://public.lindy.ai/api/v1/webhooks/YOUR_ID" \
  -H "Authorization: Bearer $LINDY_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"event": "deploy.verify", "env": "production"}'
echo "Agent triggered — check Tasks tab in Lindy dashboard"
```

### Step 6: Rollback Plan
```bash
# If deployment fails, rollback:
# Vercel
vercel rollback

# Docker
docker stop lindy-app
docker run -d --name lindy-app-rollback \
  -e LINDY_API_KEY="$LINDY_API_KEY" \
  -e LINDY_WEBHOOK_SECRET="$LINDY_WEBHOOK_SECRET" \
  lindy-integration:previous-tag

# Update Lindy agents back to previous URLs if needed
```

## Deployment Checklist

| Step | Verification |
|------|-------------|
| Build passes | `npm run build` exits 0 |
| Tests pass | `npm test` all green |
| Secrets configured | API key + webhook secret in platform |
| Health check responds | `GET /health` returns 200 |
| Webhook auth works | POST with valid token returns 200 |
| Webhook auth rejects | POST without token returns 401 |
| Lindy agent URLs updated | HTTP Request actions point to prod |
| End-to-end test | Trigger agent, receive callback |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook 502 | App crashed/not running | Check container logs, restart |
| Webhook timeout | Slow processing | Respond 200 immediately, process async |
| Wrong URL in Lindy | Not updated post-deploy | Update HTTP Request action URLs |
| SSL error | Certificate issue | Verify HTTPS cert is valid |
| Secret mismatch | Dev secret in prod | Verify production secrets match Lindy config |

## Resources
- [Lindy Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
See `lindy-webhooks-events` for advanced webhook patterns.
