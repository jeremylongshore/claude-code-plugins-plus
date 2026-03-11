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
---

# Langfuse Deploy Integration

## Overview
Deploy Langfuse LLM observability with your application. Covers integrating the Langfuse SDK for tracing, deploying self-hosted Langfuse via Docker, and configuring cloud-hosted Langfuse across Vercel, Docker, and Cloud Run deployments.

## Prerequisites
- Langfuse account (cloud at langfuse.com or self-hosted)
- Langfuse public/secret key pair
- Application using `langfuse` SDK
- Platform CLI installed

## Instructions

### Step 1: Configure Langfuse SDK
```typescript
// lib/langfuse.ts
import { Langfuse } from "langfuse";

export const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: process.env.LANGFUSE_HOST || "https://cloud.langfuse.com",
});

// Ensure traces are flushed before serverless function exits
export async function flushLangfuse() {
  await langfuse.flushAsync();
}
```

### Step 2: Vercel Deployment
```bash
vercel env add LANGFUSE_PUBLIC_KEY production
vercel env add LANGFUSE_SECRET_KEY production
vercel env add LANGFUSE_HOST production  # Optional for self-hosted
vercel --prod
```

```typescript
// api/chat.ts - Trace LLM calls
import { langfuse, flushLangfuse } from "../lib/langfuse";

export async function POST(req: Request) {
  const trace = langfuse.trace({ name: "chat-request" });

  const generation = trace.generation({
    name: "llm-call",
    model: "gpt-4o",
    input: messages,
  });

  const response = await openai.chat.completions.create({ model: "gpt-4o", messages });

  generation.end({ output: response.choices[0].message });
  await flushLangfuse();

  return Response.json(response);
}
```

### Step 3: Self-Hosted Langfuse (Docker)
```yaml
# docker-compose.yml
version: "3.8"
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3001:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/langfuse
      - NEXTAUTH_SECRET=your-secret
      - NEXTAUTH_URL=http://localhost:3001
      - SALT=your-salt
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=langfuse
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Step 4: LangChain Integration
```python
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
)

# Attach to any LangChain chain
chain.invoke({"input": "Hello"}, config={"callbacks": [langfuse_handler]})
```

### Step 5: Health Check
```typescript
export async function GET() {
  try {
    await langfuse.flushAsync();
    return Response.json({ status: "healthy", tracing: "enabled" });
  } catch {
    return Response.json({ status: "degraded", tracing: "disabled" }, { status: 503 });
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Traces not appearing | Missing flush | Call `flushAsync()` in serverless |
| Auth error | Wrong keys | Verify public/secret key pair |
| Self-hosted slow | Under-provisioned DB | Increase PostgreSQL resources |
| Missing generations | SDK not initialized | Check import and initialization |

## Examples

### Quick Integration Test
```typescript
const trace = langfuse.trace({ name: "test" });
trace.update({ output: "test complete" });
await langfuse.flushAsync();
```

## Resources
- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Self-Hosting](https://langfuse.com/docs/deployment/self-host)
- [Langfuse SDK](https://langfuse.com/docs/sdk)

## Next Steps
For webhook handling, see `langfuse-webhooks-events`.
