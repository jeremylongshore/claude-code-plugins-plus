---
name: groq-deploy-integration
description: |
  Deploy Groq integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Groq-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy groq", "groq Vercel",
  "groq production deploy", "groq Cloud Run", "groq Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Groq Deploy Integration

## Overview
Deploy applications powered by Groq's ultra-fast LLM inference API (`api.groq.com`). Groq's sub-second latency makes it ideal for real-time applications.

## Prerequisites
- Groq API key stored in `GROQ_API_KEY` environment variable
- Application using `groq-sdk` package
- Platform CLI installed (vercel, docker, or gcloud)

## Instructions

### Step 1: Configure Secrets
```bash
# Vercel (Edge-compatible)
vercel env add GROQ_API_KEY production

# Cloud Run
echo -n "your-key" | gcloud secrets create groq-api-key --data-file=-
```

### Step 2: Vercel Edge Deployment
```typescript
// api/chat.ts - Ultra-low latency with Groq + Vercel Edge
import Groq from "groq-sdk";

export const config = { runtime: "edge" };

export default async function handler(req: Request) {
  const groq = new Groq({ apiKey: process.env.GROQ_API_KEY! });
  const { messages, stream } = await req.json();

  if (stream) {
    const completion = await groq.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages,
      stream: true,
    });

    const encoder = new TextEncoder();
    const readable = new ReadableStream({
      async start(controller) {
        for await (const chunk of completion) {
          const content = chunk.choices[0]?.delta?.content;
          if (content) {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content })}\n\n`));
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
      },
    });

    return new Response(readable, {
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages,
  });

  return Response.json(completion);
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

### Step 4: Cloud Run with Streaming
```bash
gcloud run deploy groq-api \
  --source . \
  --region us-central1 \
  --set-secrets=GROQ_API_KEY=groq-api-key:latest \
  --set-env-vars=GROQ_MODEL=llama-3.3-70b-versatile \
  --min-instances=1 \
  --cpu=1 --memory=512Mi
```

### Step 5: Health Check
```typescript
export async function GET() {
  try {
    const groq = new Groq({ apiKey: process.env.GROQ_API_KEY! });
    await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "ping" }],
      max_tokens: 1,
    });
    return Response.json({ status: "healthy" });
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });  # HTTP 503 Service Unavailable
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited (429) | Too many requests | Implement request queuing |
| Model unavailable | Capacity constraint | Fall back to smaller model |
| Edge timeout | Long completion | Use streaming for long responses |
| API key invalid | Key expired | Regenerate at console.groq.com |

## Examples

**Basic usage**: Apply groq deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize groq deploy integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Models](https://console.groq.com/docs/models)

## Next Steps
For multi-environment setup, see `groq-multi-env-setup`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale