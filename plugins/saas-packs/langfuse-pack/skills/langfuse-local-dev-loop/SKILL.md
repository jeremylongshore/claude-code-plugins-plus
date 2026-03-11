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
---
# Langfuse Local Dev Loop

## Overview
Set up a fast, iterative local development workflow with Langfuse tracing and debugging.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Node.js 18+ or Python 3.9+
- Docker (optional, for self-hosted local instance)
- IDE with TypeScript/Python support

## Instructions

### Step 1: Configure Development Environment

Create a `.env.local` file for development-specific settings:

```bash
# .env.local
LANGFUSE_PUBLIC_KEY=pk-lf-dev-...
LANGFUSE_SECRET_KEY=sk-lf-dev-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Development options
LANGFUSE_DEBUG=true
LANGFUSE_FLUSH_AT=1        # Flush after every event for immediate visibility
LANGFUSE_FLUSH_INTERVAL=1000  # 1000: Flush every second
```

### Step 2: Create Debug-Enabled Client

```typescript
// src/lib/langfuse.ts
import { Langfuse } from "langfuse";

const isDev = process.env.NODE_ENV !== "production";

export const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: process.env.LANGFUSE_HOST,
  // Development settings
  flushAt: isDev ? 1 : 15,
  flushInterval: isDev ? 1000 : 10000,  # 10000: 1 second in ms
  // Enable debug logging in dev
  ...(isDev && {
    debug: true,
  }),
});

// Auto-flush on process exit
process.on("beforeExit", async () => {
  await langfuse.shutdownAsync();
});

// Helper to get trace URL immediately
export function logTraceUrl(trace: ReturnType<typeof langfuse.trace>) {
  if (isDev) {
    console.log(`\n🔍 Trace: ${trace.getTraceUrl()}\n`);
  }
}
```

### Step 3: Set Up Hot Reload Development Script

```json
// package.json
{
  "scripts": {
    "dev": "tsx watch --env-file=.env.local src/index.ts",
    "dev:debug": "DEBUG=langfuse* tsx watch --env-file=.env.local src/index.ts"
  }
}
```

### Step 4: Add Development Utilities

```typescript
// src/lib/dev-utils.ts
import { langfuse, logTraceUrl } from "./langfuse";

// Wrapper that logs trace URLs in dev
export function withTracing<T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T {
  return (async (...args: Parameters<T>) => {
    const trace = langfuse.trace({
      name,
      input: args,
      tags: ["dev"],
    });

    logTraceUrl(trace);

    try {
      const result = await fn(...args);
      trace.update({ output: result });
      return result;
    } catch (error) {
      trace.update({
        output: { error: String(error) },
        tags: ["dev", "error"],
      });
      throw error;
    }
  }) as T;
}

// Quick debug trace
export function debugTrace(name: string, data: Record<string, any>) {
  const trace = langfuse.trace({
    name: `debug/${name}`,
    metadata: data,
    tags: ["debug"],
  });
  logTraceUrl(trace);
  return trace;
}
```

## Local Self-Hosted Instance (Optional)

For completely local development without cloud:

```yaml
# docker-compose.langfuse.yml
version: "3.8"
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"  # 3000: 3 seconds in ms
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse  # 5432: PostgreSQL port
      - NEXTAUTH_SECRET=development-secret-change-in-prod
      - NEXTAUTH_URL=http://localhost:3000  # 3 seconds in ms
      - SALT=development-salt-change-in-prod
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-db:/var/lib/postgresql/data

volumes:
  langfuse-db:
```

```bash
set -euo pipefail
# Start local Langfuse
docker compose -f docker-compose.langfuse.yml up -d

# Update .env.local
echo 'LANGFUSE_HOST=http://localhost:3000' >> .env.local  # 3000: 3 seconds in ms
```

## Output
- Development environment with hot reload
- Immediate trace visibility (flush after every event)
- Debug logging enabled
- Trace URLs printed to console
- (Optional) Local Langfuse instance

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Traces delayed | Batching enabled | Set `flushAt: 1` in dev |
| No debug output | Debug not enabled | Set `LANGFUSE_DEBUG=true` |
| Hot reload fails | File watching issue | Use `tsx watch` or `nodemon` |
| Local instance unreachable | Docker not running | Run `docker compose up -d` |

## Examples

### Quick Development Test
```typescript
// src/index.ts
import { langfuse, logTraceUrl } from "./lib/langfuse";
import OpenAI from "openai";
import { observeOpenAI } from "langfuse";

const openai = observeOpenAI(new OpenAI());

async function devTest() {
  const trace = langfuse.trace({
    name: "dev-test",
    tags: ["dev"],
  });

  logTraceUrl(trace);

  const response = await openai.chat.completions.create(
    {
      model: "gpt-4",
      messages: [{ role: "user", content: "Hello!" }],
    },
    { langfuseParent: trace }
  );

  console.log("Response:", response.choices[0].message.content);
  await langfuse.flushAsync();
}

devTest();
```

### Watch Mode with Live Trace Links
```bash
set -euo pipefail
# Terminal output with trace links
$ pnpm dev

🔄 Watching for changes...

🔍 Trace: https://cloud.langfuse.com/trace/abc123...

Response: Hello! How can I help you today?

[File changed, reloading...]

🔍 Trace: https://cloud.langfuse.com/trace/def456...

Response: I'm doing great, thanks for asking!
```

### Debug Mode Configuration
```typescript
// Enable verbose SDK debugging
const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  debug: true, // Logs all SDK operations
});

// Or use environment variable
// DEBUG=langfuse* pnpm dev
```

## Resources
- [Langfuse Local Development](https://langfuse.com/docs/get-started)
- [Langfuse Self-Hosting](https://langfuse.com/docs/deployment/self-host)
- [Langfuse Docker Image](https://hub.docker.com/r/langfuse/langfuse)

## Next Steps
For SDK patterns and best practices, see `langfuse-sdk-patterns`.