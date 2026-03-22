---
name: langfuse-common-errors
description: |
  Diagnose and fix common Langfuse errors and exceptions.
  Use when encountering Langfuse errors, debugging missing traces,
  or troubleshooting integration issues.
  Trigger with phrases like "langfuse error", "fix langfuse",
  "langfuse not working", "debug langfuse", "traces not appearing".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, debugging]

---
# Langfuse Common Errors

## Overview
Diagnostic reference for the 10 most common Langfuse integration errors, with real error messages, root causes, and tested solutions.

## Prerequisites
- Langfuse SDK installed
- API credentials configured
- Access to application logs or console output

## Error Reference

### 1. Authentication Failed (401)

**Error:**
```
Langfuse: Unauthorized - Invalid API key
Error: 401 Unauthorized
```

**Cause:** API key missing, expired, revoked, or keys from wrong project.

**Fix:**
```bash
set -euo pipefail
# Verify env vars are set
echo "Public: ${LANGFUSE_PUBLIC_KEY:0:15}..."
echo "Secret: ${LANGFUSE_SECRET_KEY:0:10}..."

# Test auth against API
HOST="${LANGFUSE_BASE_URL:-https://cloud.langfuse.com}"
curl -s -o /dev/null -w "HTTP %{http_code}" \
  "$HOST/api/public/health"

# Auth test
curl -s -o /dev/null -w "HTTP %{http_code}" \
  -H "Authorization: Basic $(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)" \
  "$HOST/api/public/traces?limit=1"
```

### 2. Traces Not Appearing in Dashboard

**Symptom:** Code runs without errors but no traces show in UI.

**Root causes (in order of likelihood):**
1. Data not flushed before process exits
2. Wrong project keys (traces going to different project)
3. Dashboard filter hiding traces

**Fix:**
```typescript
// v4+: Ensure OTel SDK is shut down properly
const sdk = new NodeSDK({ spanProcessors: [new LangfuseSpanProcessor()] });
sdk.start();
// ... your code ...
await sdk.shutdown(); // MUST call this before process exits

// v3: Always flush
await langfuse.flushAsync();

// v3: Register shutdown handler for long-running processes
process.on("beforeExit", async () => {
  await langfuse.shutdownAsync();
});
```

### 3. Network / Connection Errors

**Error:**
```
FetchError: request to https://cloud.langfuse.com failed
ECONNREFUSED / ETIMEDOUT
```

**Fix:**
```bash
set -euo pipefail
# Test connectivity
curl -v https://cloud.langfuse.com/api/public/health

# Check DNS
nslookup cloud.langfuse.com

# For self-hosted
curl -v $LANGFUSE_BASE_URL/api/public/health
```

```typescript
// Increase timeout for slow networks
// v4+: Configure via OTel span processor options
// v3:
const langfuse = new Langfuse({ requestTimeout: 30000 });
```

### 4. Missing Token Usage

**Symptom:** Generations appear but token counts show zero.

**Fix:**
```typescript
// For OpenAI streaming -- enable usage reporting
const stream = await openai.chat.completions.create({
  model: "gpt-4o",
  messages,
  stream: true,
  stream_options: { include_usage: true }, // Required!
});

// For manual tracing -- always include usage on generation end
generation.end({
  output: content,
  usage: {
    promptTokens: response.usage?.prompt_tokens ?? 0,
    completionTokens: response.usage?.completion_tokens ?? 0,
  },
});

// v4+: updateActiveObservation with usage
updateActiveObservation({
  output: content,
  usage: { promptTokens: 100, completionTokens: 50 },
});
```

### 5. Spans Stuck "In Progress" (v3)

**Symptom:** Spans show as in-progress indefinitely in the dashboard.

**Fix:**
```typescript
// Always end spans in try/finally
const span = trace.span({ name: "operation" });
try {
  const result = await doWork();
  span.end({ output: result });
  return result;
} catch (error) {
  span.end({ level: "ERROR", statusMessage: String(error) });
  throw error;
}

// v4+ avoids this entirely -- startActiveObservation auto-ends
await startActiveObservation("operation", async () => {
  // Span automatically ends when callback completes or throws
  return await doWork();
});
```

### 6. Duplicate Traces

**Symptom:** Same operation creates multiple traces.

**Fix:**
```typescript
// Use singleton pattern -- NEVER create Langfuse per request
// BAD:
app.get("/api", async (req, res) => {
  const langfuse = new Langfuse(); // Creates new client per request
});

// GOOD:
const langfuse = new Langfuse(); // Single instance
app.get("/api", async (req, res) => {
  const trace = langfuse.trace({ name: "api-request" });
});
```

### 7. SDK Import Errors

**Error:**
```
TypeError: langfuse.trace is not a function
Cannot find module '@langfuse/tracing'
```

**Fix:**
```bash
set -euo pipefail
# Check installed version
npm list langfuse @langfuse/client @langfuse/tracing

# v3 import
# import { Langfuse } from "langfuse";

# v4+ imports
# import { LangfuseClient } from "@langfuse/client";
# import { startActiveObservation, observe } from "@langfuse/tracing";

# Update to latest
npm install @langfuse/client@latest @langfuse/tracing@latest @langfuse/otel@latest
```

### 8. Environment Variable Not Loaded

**Error:**
```
Langfuse: Missing required configuration - publicKey
```

**Fix:**
```typescript
// Load .env at the very top of your entry file
import "dotenv/config";

// Or use specific path
import { config } from "dotenv";
config({ path: ".env.local" });

// Validate on startup
if (!process.env.LANGFUSE_PUBLIC_KEY) {
  throw new Error("LANGFUSE_PUBLIC_KEY not set");
}
```

### 9. Self-Hosted Connection Issues

**Error:**
```
Failed to connect to localhost:3000
Certificate verification failed
```

**Fix:**
```bash
set -euo pipefail
# Check if Langfuse container is running
docker ps | grep langfuse

# Health check
curl http://localhost:3000/api/public/health

# Common issue: trailing slash in URL
# BAD:  LANGFUSE_BASE_URL=http://localhost:3000/
# GOOD: LANGFUSE_BASE_URL=http://localhost:3000
```

### 10. Rate Limiting (429)

**Error:**
```
Error: 429 Too Many Requests
Retry-After: 60
```

**Fix:**
```typescript
// v3: Increase batch size to reduce API calls
const langfuse = new Langfuse({
  flushAt: 50,         // Batch more events
  flushInterval: 30000, // Flush less often (30s)
});

// For sustained high volume, see langfuse-rate-limits skill
```

## Quick Diagnostic Script

```bash
#!/bin/bash
set -euo pipefail

echo "=== Langfuse Diagnostics ==="
echo "Node: $(node --version 2>/dev/null || echo 'N/A')"
echo "Python: $(python3 --version 2>/dev/null || echo 'N/A')"
echo ""

# SDK versions
echo "--- Installed SDK ---"
npm list langfuse @langfuse/client @langfuse/tracing 2>/dev/null || echo "npm: not found"
pip show langfuse 2>/dev/null | grep Version || echo "pip: not found"
echo ""

# Config check
echo "--- Config ---"
echo "Public Key: ${LANGFUSE_PUBLIC_KEY:+SET (${LANGFUSE_PUBLIC_KEY:0:10}...)}"
echo "Secret Key: ${LANGFUSE_SECRET_KEY:+SET}"
echo "Base URL: ${LANGFUSE_BASE_URL:-${LANGFUSE_HOST:-default cloud}}"
echo ""

# Connectivity
HOST="${LANGFUSE_BASE_URL:-${LANGFUSE_HOST:-https://cloud.langfuse.com}}"
echo "--- Connectivity ---"
echo "Health: $(curl -s -o /dev/null -w '%{http_code}' $HOST/api/public/health)"
```

## Escalation Path

1. Run diagnostic script above
2. Collect debug bundle with `langfuse-debug-bundle` skill
3. Check [Langfuse Status](https://status.langfuse.com)
4. Search [GitHub Issues](https://github.com/langfuse/langfuse/issues)
5. Ask in [Discord](https://langfuse.com/discord)

## Resources
- [Langfuse Troubleshooting](https://langfuse.com/docs/observability/get-started)
- [GitHub Issues](https://github.com/langfuse/langfuse/issues)
- [Langfuse Discord](https://langfuse.com/discord)
- [Status Page](https://status.langfuse.com)
