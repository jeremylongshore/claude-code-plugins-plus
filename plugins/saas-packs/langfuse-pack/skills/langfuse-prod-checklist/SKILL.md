---
name: langfuse-prod-checklist
description: |
  Langfuse production readiness checklist and verification.
  Use when preparing to deploy Langfuse to production,
  validating production configuration, or auditing existing setup.
  Trigger with phrases like "langfuse production", "langfuse prod ready",
  "deploy langfuse", "langfuse checklist", "langfuse go live".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Production Checklist

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive checklist for deploying Langfuse observability to production with verified configuration, error handling, graceful shutdown, and monitoring.

## Prerequisites
- Completed development and staging testing
- Access to production secrets management
- Production Langfuse project created

## Instructions

### Step 1: Verify Authentication & Security
Confirm production API keys are created, stored in a secrets manager, NOT in code/git, and isolated per environment. Verify PII scrubbing is enabled.

### Step 2: Configure SDK Settings
Set `flushAt` (15-50), `flushInterval` (5-10s), `requestTimeout` (10-30s), `enabled` (true for prod). Use singleton client pattern.

### Step 3: Implement Production Error Handling
Wrap all trace operations in try/catch. Call `.end()` in `finally` blocks. Log errors to Langfuse with ERROR level. Register `shutdownAsync()` on SIGTERM/SIGINT.

### Step 4: Run Pre-Deployment Verification
Validate env vars are set, API keys are production keys (prefix `pk-lf-`), trace creation works, and graceful shutdown completes.

### Step 5: Configure Production Monitoring
Expose metrics endpoint tracking traces created/failed, flush latency, and error rate.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Verified production configuration
- Error handling with graceful degradation
- Graceful shutdown on process signals
- Metrics endpoint for monitoring
- All checklist items validated

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing traces in prod | Flush not called | Verify shutdown handler |
| High latency | Large batches | Reduce `flushAt` |
| Memory growth | Client recreation | Use singleton pattern |
| Lost traces on deploy | No graceful shutdown | Add SIGTERM handler |

## Examples

### Production Checklist Summary
| Category | Key Items |
|----------|-----------|
| Auth & Security | Prod keys, secrets manager, env isolation, PII scrubbing |
| SDK Config | flushAt=25, flushInterval=5000, singleton client |
| Error Handling | try/catch, .end() in finally, ERROR level traces |
| Performance | Async tracing, batching, no memory leaks |
| Observability | Trace URL logging, SDK error monitoring, alerts |

### Recommended Production Config
```typescript
{
  flushAt: 25,
  flushInterval: 5000,  # 5000: 5 seconds in ms
  requestTimeout: 15000,  # 15000 = configured value
  enabled: process.env.NODE_ENV === "production",
  debug: false,
}
```

## Resources
- [Langfuse Production Guide](https://langfuse.com/docs/deployment)
- [Langfuse Self-Hosting](https://langfuse.com/docs/deployment/self-host)
- [Langfuse SDK Reference](https://langfuse.com/docs/sdk)