---
name: langfuse-local-dev-loop
description: |
  Set up Langfuse local development workflow with hot reload and debugging.
  Use when developing LLM applications locally, debugging traces,
  or setting up a fast iteration loop with Langfuse.
  Trigger with phrases like "langfuse local dev", "langfuse development",
  "debug langfuse traces", "langfuse hot reload", "langfuse dev workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Bash(pnpm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, llm, debugging, workflow]

---
# Langfuse Local Dev Loop

## Overview
Fast local development workflow with Langfuse tracing, immediate trace visibility, debug logging, and optional self-hosted local instance via Docker.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Node.js 18+ with `tsx` for hot reload (`npm install -D tsx`)
- Docker (optional, for self-hosted local instance)

## Instructions

### Step 1: Development Environment File

```bash
# .env.local (git-ignored)
LANGFUSE_PUBLIC_KEY=pk-lf-dev-...
LANGFUSE_SECRET_KEY=sk-lf-dev-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# Dev-specific settings
NODE_ENV=development
OPENAI_API_KEY=sk-...
```

### Step 2: Dev-Optimized Langfuse Setup (v4+)

```typescript
// src/lib/langfuse-dev.ts
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseClient } from "@langfuse/client";

const isDev = process.env.NODE_ENV !== "production";

// Configure span processor with dev-friendly settings
const processor = new LangfuseSpanProcessor({
  // In dev: flush immediately for instant visibility
  ...(isDev && { exportIntervalMillis: 1000, maxExportBatchSize: 1 }),
});

const sdk = new NodeSDK({ spanProcessors: [processor] });
sdk.start();

export const langfuse = new LangfuseClient();

// Print trace URLs in development
export function logTrace(traceId: string) {
  if (isDev) {
    const host = process.env.LANGFUSE_BASE_URL || "https://cloud.langfuse.com";
    console.log(`\n  Trace: ${host}/trace/${traceId}\n`);
  }
}

// Clean shutdown
process.on("SIGINT", async () => {
  await sdk.shutdown();
  process.exit(0);
});
```

### Step 3: Dev-Optimized Setup (v3 Legacy)

```typescript
// src/lib/langfuse-dev.ts
import { Langfuse } from "langfuse";

const isDev = process.env.NODE_ENV !== "production";

export const langfuse = new Langfuse({
  flushAt: isDev ? 1 : 15,          // Immediate flush in dev
  flushInterval: isDev ? 1000 : 10000,
  ...(isDev && { debug: true }),     // Verbose SDK logging
});

export function logTraceUrl(trace: ReturnType<typeof langfuse.trace>) {
  if (isDev) {
    console.log(`\n  Trace: ${trace.getTraceUrl()}\n`);
  }
}

process.on("beforeExit", async () => {
  await langfuse.shutdownAsync();
});
```

### Step 4: Hot Reload Scripts

```json
{
  "scripts": {
    "dev": "tsx watch --env-file=.env.local src/index.ts",
    "dev:debug": "DEBUG=langfuse* tsx watch --env-file=.env.local src/index.ts",
    "dev:trace": "LANGFUSE_DEBUG=true tsx watch --env-file=.env.local src/index.ts"
  }
}
```

### Step 5: Development Tracing Utilities

```typescript
// src/lib/dev-utils.ts
import { observe, updateActiveObservation, startActiveObservation } from "@langfuse/tracing";

// Quick traced function wrapper with console output
export function devTrace<T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T {
  return observe({ name }, async (...args: Parameters<T>) => {
    updateActiveObservation({ input: args, metadata: { env: "dev" } });
    const start = Date.now();

    const result = await fn(...args);

    const duration = Date.now() - start;
    updateActiveObservation({ output: result });
    console.log(`  [${name}] ${duration}ms`);

    return result;
  }) as T;
}

// Quick debug trace -- fire-and-forget diagnostic trace
export async function debugTrace(name: string, data: Record<string, any>) {
  await startActiveObservation(`debug/${name}`, async () => {
    updateActiveObservation({
      input: data,
      metadata: { debug: true, timestamp: new Date().toISOString() },
    });
  });
}
```

### Step 6: Example Dev Workflow

```typescript
// src/index.ts
import "dotenv/config";
import { initTracing, langfuse } from "./lib/langfuse-dev";
import { devTrace } from "./lib/dev-utils";
import OpenAI from "openai";
import { observeOpenAI } from "@langfuse/openai";

initTracing();

const openai = observeOpenAI(new OpenAI());

const askQuestion = devTrace("ask-question", async (question: string) => {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: question }],
  });
  return response.choices[0].message.content;
});

// Run on file save (tsx watch restarts automatically)
const answer = await askQuestion("What is Langfuse?");
console.log("Answer:", answer);
```

## Local Self-Hosted Langfuse (Optional)

For offline development or data privacy:

```yaml
# docker-compose.langfuse.yml
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
      - NEXTAUTH_SECRET=dev-secret-change-in-prod
      - NEXTAUTH_URL=http://localhost:3000
      - SALT=dev-salt-change-in-prod
      - ENCRYPTION_KEY=0000000000000000000000000000000000000000000000000000000000000000
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: langfuse
    volumes:
      - langfuse-db:/var/lib/postgresql/data

volumes:
  langfuse-db:
```

```bash
set -euo pipefail
# Start local Langfuse
docker compose -f docker-compose.langfuse.yml up -d

# Wait for startup, then visit http://localhost:3000
# Create account, project, and API keys in the local UI

# Update .env.local
echo 'LANGFUSE_BASE_URL=http://localhost:3000' >> .env.local
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Traces delayed in dev | Batching still active | Set `flushAt: 1` or `exportIntervalMillis: 1000` |
| No debug output | Debug not enabled | Set `LANGFUSE_DEBUG=true` or `DEBUG=langfuse*` |
| Hot reload not working | Wrong watch command | Use `tsx watch` (not `ts-node`) |
| Local instance 502 | DB not ready | Wait 10s for PostgreSQL startup |
| Traces going to cloud | Wrong `LANGFUSE_BASE_URL` | Point to `http://localhost:3000` |

## Resources
- [TypeScript SDK Setup](https://langfuse.com/docs/observability/sdk/typescript/setup)
- [Self-Hosting Docker Compose](https://langfuse.com/self-hosting/deployment/docker-compose)
- [Advanced SDK Configuration](https://langfuse.com/docs/observability/sdk/typescript/advanced-usage)

## Next Steps
For SDK patterns and best practices, see `langfuse-sdk-patterns`.
