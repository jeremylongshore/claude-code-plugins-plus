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
---
# Langfuse Common Errors

## Overview
Quick reference for the top 10 most common Langfuse errors and their solutions.

## Prerequisites
- Langfuse SDK installed
- API credentials configured
- Access to error logs

## Instructions

### Step 1: Identify the Error
Check error message and code in your logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Output
- Identified error cause
- Applied fix
- Verified resolution

## Error Handling

### 1. Authentication Failed
**Error Message:**
```
Langfuse: Unauthorized - Invalid API key
Error: 401 Unauthorized  # HTTP 401 Unauthorized
```

**Cause:** API key is missing, expired, or mismatched with host.

**Solution:**
```bash
set -euo pipefail
# Verify environment variables are set
echo "Public: $LANGFUSE_PUBLIC_KEY"
echo "Secret: ${LANGFUSE_SECRET_KEY:0:10}..."  # Partial for security
echo "Host: $LANGFUSE_HOST"

# Test connection
curl -X GET "$LANGFUSE_HOST/api/public/health" \
  -H "Authorization: Basic $(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)"
```

---

### 2. Traces Not Appearing in Dashboard
**Symptom:** Code runs without errors but traces don't show up.

**Cause:** Data not flushed before process exits.

**Solution:**
```typescript
// Always flush before exit
await langfuse.flushAsync();

// Or use shutdown for clean exit
await langfuse.shutdownAsync();

// Register shutdown handler
process.on("beforeExit", async () => {
  await langfuse.shutdownAsync();
});
```

---

### 3. Network/Connection Errors
**Error Message:**
```
FetchError: request to https://cloud.langfuse.com failed
ECONNREFUSED / ETIMEDOUT
```

**Cause:** Network connectivity or firewall issues.

**Solution:**
```bash
set -euo pipefail
# Test connectivity
curl -v https://cloud.langfuse.com/api/public/health

# Check DNS resolution
nslookup cloud.langfuse.com

# For self-hosted, verify host URL
curl -v $LANGFUSE_HOST/api/public/health
```

```typescript
// Increase timeout if needed
const langfuse = new Langfuse({
  requestTimeout: 30000, // 30 seconds  # 30000: 30 seconds in ms
});
```

---

### 4. Missing Token Usage
**Symptom:** Generations appear but token counts are 0.

**Cause:** Usage data not captured from LLM response.

**Solution:**
```typescript
// For streaming, enable usage in options
const stream = await openai.chat.completions.create({
  model: "gpt-4",
  messages,
  stream: true,
  stream_options: { include_usage: true }, // Important!
});

// Manually add usage if not available
generation.end({
  output: content,
  usage: {
    promptTokens: response.usage?.prompt_tokens || 0,
    completionTokens: response.usage?.completion_tokens || 0,
  },
});
```

---

### 5. Trace/Span Not Ending
**Symptom:** Traces show as "in progress" indefinitely.

**Cause:** Missing `.end()` call on spans/generations.

**Solution:**
```typescript
// Always end in try/finally
const span = trace.span({ name: "operation" });
try {
  const result = await doWork();
  span.end({ output: result });
  return result;
} catch (error) {
  span.end({ level: "ERROR", statusMessage: String(error) });
  throw error;
}

// Or use finally
const span = trace.span({ name: "operation" });
try {
  return await doWork();
} finally {
  span.end();
}
```

---

### 6. Duplicate Traces
**Symptom:** Same operation creates multiple traces.

**Cause:** Client instantiated multiple times or missing singleton.

**Solution:**
```typescript
// Use singleton pattern
let langfuseInstance: Langfuse | null = null;

export function getLangfuse(): Langfuse {
  if (!langfuseInstance) {
    langfuseInstance = new Langfuse();
  }
  return langfuseInstance;
}

// Don't create new instance per request
// BAD: const langfuse = new Langfuse(); // in handler
// GOOD: const langfuse = getLangfuse();
```

---

### 7. SDK Version Mismatch
**Error Message:**
```
TypeError: langfuse.trace is not a function
Property 'observeOpenAI' does not exist
```

**Cause:** Outdated SDK or breaking API change.

**Solution:**
```bash
set -euo pipefail
# Check current version
npm list langfuse

# Update to latest
npm install langfuse@latest

# Check changelog for breaking changes
# https://github.com/langfuse/langfuse-js/releases
```

---

### 8. Environment Variable Not Loaded
**Error Message:**
```
Langfuse: Missing required configuration - publicKey
```

**Cause:** .env file not loaded or wrong variable names.

**Solution:**
```bash
# Verify .env file exists and has correct names
cat .env | grep LANGFUSE

# Required variable names:
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_HOST=https://cloud.langfuse.com
```

```typescript
// Load .env in your app
import "dotenv/config"; // At top of entry file

// Or specify env file
import { config } from "dotenv";
config({ path: ".env.local" });
```

---

### 9. Self-Hosted Connection Issues
**Error Message:**
```
Failed to connect to localhost:3000  # 3000: 3 seconds in ms
Certificate verification failed
```

**Cause:** Self-hosted instance not running or SSL issues.

**Solution:**
```bash
set -euo pipefail
# Check if Langfuse is running
docker ps | grep langfuse
curl http://localhost:3000/api/public/health  # 3000: 3 seconds in ms

# For HTTPS without valid cert
export NODE_TLS_REJECT_UNAUTHORIZED=0  # Development only!
```

```typescript
// Verify host URL doesn't have trailing slash
const langfuse = new Langfuse({
  baseUrl: "http://localhost:3000", // No trailing slash  # 3000: 3 seconds in ms
});
```

---

### 10. Rate Limiting
**Error Message:**
```
Error: 429 Too Many Requests  # HTTP 429 Too Many Requests
Retry-After: 60
```

**Cause:** Exceeded Langfuse API rate limits.

**Solution:**
```typescript
// Increase batch size to reduce requests
const langfuse = new Langfuse({
  flushAt: 50,        // Batch more events
  flushInterval: 30000, // Flush less often  # 30000: 30 seconds in ms
});

// See langfuse-rate-limits skill for advanced handling
```

## Quick Diagnostic Commands
```bash
set -euo pipefail
# Check Langfuse cloud status
curl -s https://status.langfuse.com

# Verify API connectivity
curl -I https://cloud.langfuse.com/api/public/health

# Check local environment
env | grep LANGFUSE

# Test auth
curl -X GET "https://cloud.langfuse.com/api/public/traces" \
  -H "Authorization: Basic $(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)" \
  | head -c 200  # HTTP 200 OK
```

## Escalation Path
1. Collect evidence with `langfuse-debug-bundle`
2. Check [Langfuse Status](https://status.langfuse.com)
3. Search [GitHub Issues](https://github.com/langfuse/langfuse/issues)
4. Join [Discord Community](https://langfuse.com/discord)
5. Contact support with debug bundle

## Resources
- [Langfuse Troubleshooting](https://langfuse.com/docs/get-started)
- [Langfuse GitHub Issues](https://github.com/langfuse/langfuse/issues)
- [Langfuse Discord](https://langfuse.com/discord)

## Next Steps
For comprehensive debugging, see `langfuse-debug-bundle`.

## Examples

**Basic usage**: Apply langfuse common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize langfuse common errors for production environments with multiple constraints and team-specific requirements.