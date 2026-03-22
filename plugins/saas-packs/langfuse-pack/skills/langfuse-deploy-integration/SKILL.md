---
name: langfuse-deploy-integration
description: |
  Deploy Langfuse with your application across different platforms.
  Use when deploying Langfuse to Vercel, AWS, GCP, or Docker,
  or integrating Langfuse into your deployment pipeline.
  Trigger with phrases like "deploy langfuse", "langfuse Vercel",
  "langfuse AWS", "langfuse Docker", "langfuse production deploy".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(vercel:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, deployment, docker]

---
# Langfuse Deploy Integration

## Overview
Deploy Langfuse LLM observability alongside your application. Covers integrating the SDK for serverless (Vercel/Lambda), Docker, Cloud Run, and self-hosting the Langfuse server itself.

## Prerequisites
- Langfuse API keys (cloud or self-hosted)
- Application using Langfuse SDK
- Target platform CLI installed

## Instructions

### Step 1: Vercel / Next.js Deployment

```bash
set -euo pipefail
# Add secrets to Vercel
vercel env add LANGFUSE_PUBLIC_KEY production
vercel env add LANGFUSE_SECRET_KEY production
vercel env add LANGFUSE_BASE_URL production
```

```typescript
// app/api/chat/route.ts (Next.js App Router)
import { NextRequest, NextResponse } from "next/server";
import { LangfuseClient } from "@langfuse/client";
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";
import OpenAI from "openai";

const langfuse = new LangfuseClient();
const openai = new OpenAI();

export async function POST(req: NextRequest) {
  const { messages } = await req.json();

  const response = await startActiveObservation(
    { name: "chat-api", asType: "generation" },
    async () => {
      updateActiveObservation({
        model: "gpt-4o",
        input: messages,
        metadata: { endpoint: "/api/chat" },
      });

      const result = await openai.chat.completions.create({
        model: "gpt-4o",
        messages,
      });

      updateActiveObservation({
        output: result.choices[0].message,
        usage: {
          promptTokens: result.usage?.prompt_tokens,
          completionTokens: result.usage?.completion_tokens,
        },
      });

      return result.choices[0].message;
    }
  );

  return NextResponse.json(response);
}
```

> **Serverless note:** Langfuse SDK v4+ uses OTel which handles flushing asynchronously. For v3, always call `await langfuse.flushAsync()` before the response returns -- serverless functions may freeze after response.

### Step 2: AWS Lambda / Serverless

```typescript
// handler.ts
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

// Initialize OUTSIDE handler for connection reuse
const sdk = new NodeSDK({
  spanProcessors: [
    new LangfuseSpanProcessor({
      exportIntervalMillis: 1000, // Flush fast in serverless
    }),
  ],
});
sdk.start();

export const handler = async (event: any) => {
  return await startActiveObservation("lambda-handler", async () => {
    updateActiveObservation({ input: event });

    const result = await processRequest(event);

    updateActiveObservation({ output: result });

    // Force flush before Lambda freezes
    await sdk.shutdown();

    return { statusCode: 200, body: JSON.stringify(result) };
  });
};
```

### Step 3: Self-Hosted Langfuse Server (Docker)

```yaml
# docker-compose.yml
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://langfuse:${DB_PASSWORD}@postgres:5432/langfuse
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXTAUTH_URL=https://langfuse.your-domain.com
      - SALT=${SALT}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - AUTH_DISABLE_SIGNUP=true
      - LANGFUSE_DEFAULT_PROJECT_ROLE=VIEWER
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: langfuse
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langfuse"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

```bash
set -euo pipefail
# Generate secrets
export DB_PASSWORD=$(openssl rand -hex 16)
export NEXTAUTH_SECRET=$(openssl rand -hex 32)
export SALT=$(openssl rand -hex 16)
export ENCRYPTION_KEY=$(openssl rand -hex 32)

# Start
docker compose up -d

# Wait and verify
sleep 10
curl -s http://localhost:3000/api/public/health
```

### Step 4: Google Cloud Run

```bash
set -euo pipefail
# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/my-llm-app

# Deploy with Langfuse env vars from Secret Manager
gcloud run deploy my-llm-app \
  --image gcr.io/$PROJECT_ID/my-llm-app \
  --set-secrets="LANGFUSE_PUBLIC_KEY=langfuse-public-key:latest" \
  --set-secrets="LANGFUSE_SECRET_KEY=langfuse-secret-key:latest" \
  --set-env-vars="LANGFUSE_BASE_URL=https://cloud.langfuse.com"
```

### Step 5: Health Check Endpoint

```typescript
// app/api/health/route.ts
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();

export async function GET() {
  try {
    // Quick connectivity check
    await langfuse.prompt.get("__health__").catch(() => {});
    return Response.json({ status: "healthy", tracing: "enabled" });
  } catch {
    return Response.json(
      { status: "degraded", tracing: "disabled" },
      { status: 503 }
    );
  }
}
```

## Platform-Specific Considerations

| Platform | Key Concern | Solution |
|----------|-------------|----------|
| Vercel/Edge | Function timeout | Flush before response; use v4+ |
| AWS Lambda | Cold starts | Initialize SDK outside handler |
| Cloud Run | Concurrency | Singleton client, shared OTel SDK |
| Docker | Self-hosted networking | Ensure app can reach Langfuse host |
| Kubernetes | Pod lifecycle | Shutdown hook on SIGTERM |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Traces missing in serverless | Not flushed before freeze | `sdk.shutdown()` before response |
| Auth error after deploy | Wrong env for environment | Verify secrets match deployment |
| Self-hosted 502 | DB not ready | Add healthcheck + `depends_on` |
| High latency in prod | Small batch size | Increase `flushAt` / `maxExportBatchSize` |

## Resources
- [Self-Hosting Docker Compose](https://langfuse.com/self-hosting/deployment/docker-compose)
- [Self-Hosting Configuration](https://langfuse.com/self-hosting/configuration)
- [TypeScript SDK Setup](https://langfuse.com/docs/observability/sdk/typescript/setup)
