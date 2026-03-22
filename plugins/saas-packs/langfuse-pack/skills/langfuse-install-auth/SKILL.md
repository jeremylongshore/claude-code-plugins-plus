---
name: langfuse-install-auth
description: |
  Install and configure Langfuse SDK authentication for LLM observability.
  Use when setting up a new Langfuse integration, configuring API keys,
  or initializing Langfuse tracing in your project.
  Trigger with phrases like "install langfuse", "setup langfuse",
  "langfuse auth", "configure langfuse API key", "langfuse tracing setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, api, observability, llm]

---
# Langfuse Install & Auth

## Overview
Install the Langfuse SDK and configure authentication for LLM observability. Covers both the legacy `langfuse` package (v3) and the modern modular SDK (v4+/v5) built on OpenTelemetry.

## Prerequisites
- Node.js 18+ or Python 3.9+
- Package manager (npm, pnpm, or pip)
- Langfuse account (cloud at https://cloud.langfuse.com or self-hosted)
- Public Key (`pk-lf-...`) and Secret Key (`sk-lf-...`) from project settings

## Instructions

### Step 1: Install SDK

**TypeScript/JavaScript (v4+ modular SDK -- recommended):**
```bash
set -euo pipefail
# Core client for prompt management, datasets, scores
npm install @langfuse/client

# Tracing (observe, startActiveObservation)
npm install @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node

# OpenAI integration (drop-in wrapper)
npm install @langfuse/openai

# LangChain integration
npm install @langfuse/langchain
```

**TypeScript/JavaScript (v3 legacy -- single package):**
```bash
npm install langfuse
```

**Python:**
```bash
pip install langfuse
```

### Step 2: Get API Keys

1. Open Langfuse dashboard (https://cloud.langfuse.com or your self-hosted URL)
2. Go to **Settings > API Keys**
3. Click **Create new API key pair**
4. Copy both keys:
   - **Public Key**: `pk-lf-...` (identifies your project)
   - **Secret Key**: `sk-lf-...` (grants write access -- keep secret)
5. Note the host URL (cloud default: `https://cloud.langfuse.com`)

### Step 3: Configure Environment Variables

```bash
# Set environment variables
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"

# Or create .env file
cat >> .env << 'EOF'
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
EOF
```

> **Note:** v4+ uses `LANGFUSE_BASE_URL`. Legacy v3 uses `LANGFUSE_HOST` or `LANGFUSE_BASEURL`.

### Step 4: Initialize and Verify (v4+ Modular SDK)

```typescript
// src/lib/langfuse.ts
import { LangfuseClient } from "@langfuse/client";
import { startActiveObservation } from "@langfuse/tracing";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

// 1. Register the OpenTelemetry span processor (once at app startup)
const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});
sdk.start();

// 2. Create the Langfuse client for prompt/dataset/score operations
export const langfuse = new LangfuseClient({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL,
});

// 3. Verify connection
async function verify() {
  await startActiveObservation("connection-test", async (span) => {
    span.update({ input: { test: true } });
    span.update({ output: { status: "connected" } });
  });
  console.log("Langfuse connection verified. Check dashboard for trace.");
}

verify();
```

### Step 5: Initialize and Verify (v3 Legacy SDK)

```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_HOST,
});

// Verify with a test trace
const trace = langfuse.trace({
  name: "connection-test",
  metadata: { test: true },
});

await langfuse.flushAsync();
console.log("Connected. Trace URL:", trace.getTraceUrl());

// Clean shutdown
process.on("beforeExit", async () => {
  await langfuse.shutdownAsync();
});
```

### Step 6: Python Verification

```python
from langfuse import Langfuse
import os

langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
)

# Test trace
trace = langfuse.trace(name="connection-test", metadata={"test": True})
langfuse.flush()
print(f"Connected. Trace: {trace.get_trace_url()}")
```

## SDK Version Comparison

| Feature | v3 (`langfuse`) | v4+ (`@langfuse/*`) |
|---------|-----------------|---------------------|
| Package | Single `langfuse` | Modular: `@langfuse/client`, `@langfuse/tracing`, `@langfuse/otel` |
| Base URL env var | `LANGFUSE_HOST` | `LANGFUSE_BASE_URL` |
| Tracing | `langfuse.trace()` | `startActiveObservation()` / `observe()` |
| Client class | `Langfuse` | `LangfuseClient` |
| OpenAI wrapper | `observeOpenAI()` from `langfuse` | `observeOpenAI()` from `@langfuse/openai` |
| Foundation | Custom | OpenTelemetry |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Re-check keys in Langfuse dashboard Settings > API Keys |
| `ECONNREFUSED` | Wrong host URL or server down | Verify `LANGFUSE_BASE_URL` / `LANGFUSE_HOST` |
| `Missing required configuration` | Env vars not loaded | Ensure `dotenv/config` imported at entry point |
| `Module not found` | Package not installed | Run `npm install` or `pip install` again |
| Using pk- key as secret | Keys swapped | Public key starts `pk-lf-`, secret starts `sk-lf-` |

## Resources
- [TypeScript SDK Setup](https://langfuse.com/docs/observability/sdk/typescript/setup)
- [Python SDK Setup](https://langfuse.com/docs/sdk/python/decorators)
- [v3 to v4 Migration Guide](https://langfuse.com/docs/observability/sdk/upgrade-path/js-v3-to-v4)
- [Self-Hosting Configuration](https://langfuse.com/self-hosting/configuration)

## Next Steps
After auth is working, proceed to `langfuse-hello-world` for your first traced LLM call.
