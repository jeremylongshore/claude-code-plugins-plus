---
name: langfuse-upgrade-migration
description: |
  Upgrade Langfuse SDK versions and migrate between API changes.
  Use when upgrading Langfuse SDK, handling breaking changes,
  or migrating between Langfuse versions.
  Trigger with phrases like "upgrade langfuse", "langfuse migration",
  "update langfuse SDK", "langfuse breaking changes", "langfuse version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, api, migration]

---
# Langfuse Upgrade & Migration

## Current State
!`npm list langfuse @langfuse/client @langfuse/tracing @langfuse/otel 2>/dev/null | head -10 || echo 'No langfuse packages found'`
!`pip show langfuse 2>/dev/null | grep -E "Name|Version" || echo 'Python langfuse not installed'`

## Overview
Step-by-step guide for upgrading the Langfuse SDK across major versions. Covers v3 to v4 (OTel rewrite), v4 to v5, breaking changes, and automated codemods.

## Prerequisites
- Existing Langfuse integration
- Test suite covering traced operations
- Git branch for the upgrade

## Version Roadmap

| SDK | Package | Architecture | Status |
|-----|---------|-------------|--------|
| v3 | `langfuse` (single) | Custom, `Langfuse` class | Legacy |
| v4 | `@langfuse/client`, `@langfuse/tracing`, `@langfuse/otel` | OpenTelemetry-based | Stable |
| v5 | `@langfuse/client`, `@langfuse/tracing`, `@langfuse/otel` | OpenTelemetry + improvements | Latest |

## Instructions

### Step 1: Check Current Version and Plan

```bash
set -euo pipefail
# Check what you have
npm list langfuse @langfuse/client @langfuse/tracing 2>/dev/null

# Check latest available
npm info @langfuse/client version
npm info @langfuse/tracing version
npm info langfuse version

# Python
pip show langfuse 2>/dev/null | grep Version
pip index versions langfuse 2>/dev/null | head -3
```

### Step 2: v3 to v4 Migration (TypeScript)

This is the biggest migration -- v4 rewrites tracing on OpenTelemetry.

**2a. Install new packages:**
```bash
set -euo pipefail
# Install v4+ packages
npm install @langfuse/client @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node

# Keep langfuse v3 temporarily for comparison
# Remove after migration: npm uninstall langfuse
```

**2b. Update initialization:**
```typescript
// BEFORE (v3):
import { Langfuse } from "langfuse";
const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_HOST,
});

// AFTER (v4+):
import { LangfuseClient } from "@langfuse/client";
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

// OTel setup (once at entry point)
const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});
sdk.start();

// Client for prompts, datasets, scores
const langfuse = new LangfuseClient();
```

**2c. Update tracing calls:**
```typescript
// BEFORE (v3): Manual trace/span/generation
const trace = langfuse.trace({ name: "my-op", input: data });
const span = trace.span({ name: "step-1", input: data });
await doWork();
span.end({ output: result });
const gen = trace.generation({ name: "llm", model: "gpt-4o" });
gen.end({ output: response, usage: { promptTokens: 10 } });
await langfuse.flushAsync();

// AFTER (v4+): startActiveObservation with auto-nesting
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

await startActiveObservation("my-op", async () => {
  updateActiveObservation({ input: data });

  await startActiveObservation("step-1", async () => {
    updateActiveObservation({ input: data });
    const result = await doWork();
    updateActiveObservation({ output: result });
  });

  await startActiveObservation({ name: "llm", asType: "generation" }, async () => {
    updateActiveObservation({ model: "gpt-4o" });
    const response = await callLLM();
    updateActiveObservation({ output: response, usage: { promptTokens: 10 } });
  });
});
```

**2d. Update OpenAI wrapper:**
```typescript
// BEFORE (v3):
import { observeOpenAI } from "langfuse";

// AFTER (v4+):
import { observeOpenAI } from "@langfuse/openai";
// npm install @langfuse/openai
```

**2e. Update environment variable:**
```bash
# BEFORE: LANGFUSE_HOST or LANGFUSE_BASEURL
# AFTER:  LANGFUSE_BASE_URL (LANGFUSE_BASEURL still works in v4 but not v5)
```

**2f. Update prompt management:**
```typescript
// BEFORE (v3):
const prompt = await langfuse.getPrompt("my-prompt", 2); // version as positional arg

// AFTER (v4+):
const prompt = await langfuse.prompt.get("my-prompt", {
  version: 2, // version in options object
  type: "text", // explicit type
});
```

**2g. Update shutdown:**
```typescript
// BEFORE (v3):
await langfuse.shutdownAsync();

// AFTER (v4+):
await sdk.shutdown(); // Shuts down OTel SDK + flushes spans
```

### Step 3: Python SDK Migration (v2 to v3)

```python
# BEFORE (v2):
from langfuse import Langfuse
langfuse = Langfuse()

@langfuse.observe()
def my_function():
    pass

# AFTER (v3):
from langfuse.decorators import observe, langfuse_context

@observe()
def my_function():
    langfuse_context.update_current_observation(
        metadata={"key": "value"}
    )
```

### Step 4: Run Tests and Verify

```bash
set -euo pipefail
# Run existing test suite
npm test

# Verify traces appear in dashboard
node -e "
  const { startActiveObservation, updateActiveObservation } = require('@langfuse/tracing');
  startActiveObservation('upgrade-verify', async () => {
    updateActiveObservation({ input: { test: true }, output: { migrated: true } });
  }).then(() => console.log('Migration verified'));
"
```

### Step 5: Remove Old Package

```bash
set -euo pipefail
# After all tests pass
npm uninstall langfuse

# Verify no lingering imports
grep -rn "from ['\"]langfuse['\"]" src/ || echo "No old imports found"
```

## Breaking Changes Quick Reference

| Change | v3 | v4+ |
|--------|-------|-------|
| Package | `langfuse` | `@langfuse/client` + `@langfuse/tracing` + `@langfuse/otel` |
| Client class | `Langfuse` | `LangfuseClient` |
| Base URL env | `LANGFUSE_HOST` | `LANGFUSE_BASE_URL` |
| Tracing | `langfuse.trace()` / `.span()` / `.generation()` | `startActiveObservation()` / `observe()` |
| Flush | `langfuse.flushAsync()` | `sdk.shutdown()` |
| Prompt version | `getPrompt(name, version)` | `prompt.get(name, { version })` |
| OpenAI | `import { observeOpenAI } from "langfuse"` | `import { observeOpenAI } from "@langfuse/openai"` |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot find module '@langfuse/tracing'` | Package not installed | `npm install @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node` |
| `langfuse.trace is not a function` | Using v4 `LangfuseClient` for tracing | Use `startActiveObservation` from `@langfuse/tracing` |
| Flat traces (no nesting) | OTel SDK not started | Register `LangfuseSpanProcessor` with `NodeSDK` |
| `LANGFUSE_HOST` ignored | v5 dropped legacy env var | Rename to `LANGFUSE_BASE_URL` |

## Resources
- [v3 to v4 Migration Guide](https://langfuse.com/docs/observability/sdk/upgrade-path/js-v3-to-v4)
- [v4 to v5 Migration Guide](https://langfuse.com/docs/observability/sdk/upgrade-path/js-v4-to-v5)
- [Python v3 to v4 Migration](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4)
- [TypeScript SDK v4 Changelog](https://langfuse.com/changelog/2025-08-28-typescript-sdk-v4-ga)
