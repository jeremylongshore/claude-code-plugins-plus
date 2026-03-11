---
name: fireflies-deploy-integration
description: |
  Deploy Fireflies.ai integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Fireflies.ai-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy fireflies", "fireflies Vercel",
  "fireflies production deploy", "fireflies Cloud Run", "fireflies Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies.ai Deploy Integration

## Overview
Deploy applications that integrate with Fireflies.ai's meeting transcription service. Covers configuring the GraphQL API connection, deploying webhook receivers for transcript notifications, and managing API credentials across deployment platforms.

## Prerequisites
- Fireflies.ai account with API access (Business or Enterprise plan)
- Fireflies API key stored in `FIREFLIES_API_KEY` environment variable
- Platform CLI installed (vercel, docker, or gcloud)
- GraphQL client for Fireflies API at `api.fireflies.ai/graphql`

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel
vercel env add FIREFLIES_API_KEY production

# Docker
echo "FIREFLIES_API_KEY=your-key" >> .env.production
```

### Step 2: GraphQL Client Setup
```typescript
// lib/fireflies.ts
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

export async function firefliesQuery(query: string, variables?: any) {
  const response = await fetch(FIREFLIES_API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${process.env.FIREFLIES_API_KEY}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  const result = await response.json();
  if (result.errors) throw new Error(result.errors[0].message);
  return result.data;
}
```

### Step 3: Deploy Webhook Receiver
```typescript
// api/webhooks/fireflies.ts
export async function POST(req: Request) {
  const { event_type, meeting_id, data } = await req.json();

  if (event_type === "Transcription completed") {
    const transcript = await firefliesQuery(`
      query { transcript(id: "${meeting_id}") {
        title duration speakers { name } summary { overview action_items }
      }}
    `);
    await processTranscript(transcript);
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
    await firefliesQuery("{ user { email } }");
    return Response.json({ status: "healthy", service: "fireflies" });
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });  # HTTP 503 Service Unavailable
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| GraphQL auth error | Invalid API key | Regenerate key in Fireflies dashboard |
| No transcripts | Bot not invited | Ensure Fireflies bot joins meetings |
| Webhook not firing | Webhook not registered | Register via GraphQL mutation |
| Query timeout | Large transcript | Paginate results or request specific fields |

## Examples

### Register Webhook
```bash
set -euo pipefail
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { addWebhook(input: { url: \"https://api.yourapp.com/webhooks/fireflies\", events: [\"Transcription completed\"] }) { id } }"}'
```

## Resources
- [Fireflies API Documentation](https://docs.fireflies.ai/api)
- [Fireflies GraphQL Reference](https://docs.fireflies.ai/graphql)

## Next Steps
For webhook handling, see `fireflies-webhooks-events`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale