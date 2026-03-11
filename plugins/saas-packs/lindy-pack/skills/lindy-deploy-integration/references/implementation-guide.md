# Lindy Deploy Integration - Implementation Guide

# Lindy AI Deploy Integration

## Overview
Deploy Lindy AI agent integrations to production environments. Lindy agents run on Lindy's managed infrastructure, so deployment focuses on configuring your application's connection to Lindy agents, managing API credentials, and setting up webhook endpoints that Lindy agents interact with.

## Prerequisites
- Lindy account with agents configured
- Lindy API key stored in `LINDY_API_KEY` environment variable
- Application endpoints ready for Lindy agent callbacks
- Deployment platform CLI (Vercel, Docker, etc.)

## Instructions

### Step 1: Configure Agent Connection
```typescript
// config/lindy.ts
interface LindyConfig {
  apiKey: string;
  agentIds: Record<string, string>;
  webhookUrl: string;
}

export function getLindyConfig(): LindyConfig {
  return {
    apiKey: process.env.LINDY_API_KEY!,
    agentIds: {
      emailDrafter: process.env.LINDY_EMAIL_AGENT_ID!,
      researcher: process.env.LINDY_RESEARCH_AGENT_ID!,
      scheduler: process.env.LINDY_SCHEDULER_AGENT_ID!,
    },
    webhookUrl: process.env.LINDY_WEBHOOK_URL!,
  };
}
```

### Step 2: Docker Deployment
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

```bash
docker build -t lindy-integration .
docker run -d \
  -e LINDY_API_KEY="$LINDY_API_KEY" \
  -e LINDY_EMAIL_AGENT_ID="$LINDY_EMAIL_AGENT_ID" \
  -e LINDY_WEBHOOK_URL="https://api.yourapp.com/webhooks/lindy" \
  -p 3000:3000 \
  lindy-integration
```

### Step 3: Vercel Deployment
```bash
vercel env add LINDY_API_KEY production
vercel env add LINDY_EMAIL_AGENT_ID production
vercel env add LINDY_WEBHOOK_URL production

vercel --prod
```

### Step 4: Production Agent Trigger
```typescript
async function triggerLindyAgent(agentId: string, input: any) {
  const config = getLindyConfig();

  const response = await fetch(`https://api.lindy.ai/v1/agents/${agentId}/run`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      input,
      webhook_url: config.webhookUrl,
    }),
  });

  return response.json();
}
```

### Step 5: Health Check
```typescript
export async function GET() {
  try {
    const response = await fetch("https://api.lindy.ai/v1/agents", {
      headers: { "Authorization": `Bearer ${process.env.LINDY_API_KEY}` },
    });
    return Response.json({ status: response.ok ? "healthy" : "degraded" });
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent not found | Invalid agent ID | Verify agent IDs in Lindy dashboard |
| Webhook unreachable | Wrong URL or HTTPS | Ensure public HTTPS endpoint |
| API key invalid | Key revoked | Regenerate in Lindy settings |
| Agent timeout | Complex task | Increase agent timeout in Lindy config |

## Examples

### Deploy Script
```bash
#!/bin/bash
set -e
npm run build
npm run test
vercel --prod
echo "Deployed. Verify webhook: curl -s https://api.yourapp.com/health"
```

## Resources
- [Lindy AI Documentation](https://docs.lindy.ai)
- [Lindy API Reference](https://docs.lindy.ai/api)

## Next Steps
For webhook handling, see `lindy-webhooks-events`.
