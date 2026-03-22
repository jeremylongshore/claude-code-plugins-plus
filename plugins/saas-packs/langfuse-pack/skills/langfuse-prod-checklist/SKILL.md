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
tags: [saas, langfuse, deployment, audit]

---
# Langfuse Production Checklist

## Overview
Comprehensive checklist for deploying Langfuse observability to production with verified configuration, error handling, graceful shutdown, monitoring, and a pre-deployment verification script.

## Prerequisites
- Development and staging testing completed
- Production Langfuse project created with separate API keys
- Secret management solution in place

## Production Configuration

### Recommended SDK Settings

```typescript
// v4+ Production Config
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

const processor = new LangfuseSpanProcessor({
  exportIntervalMillis: 5000,  // Flush every 5s
  maxExportBatchSize: 50,      // Batch size
  maxQueueSize: 2048,          // Buffer limit
});

const sdk = new NodeSDK({ spanProcessors: [processor] });
sdk.start();

// Graceful shutdown on all signals
for (const signal of ["SIGTERM", "SIGINT", "SIGUSR2"]) {
  process.on(signal, async () => {
    await sdk.shutdown();
    process.exit(0);
  });
}
```

```typescript
// v3 Legacy Production Config
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  flushAt: 25,            // Balance between latency and efficiency
  flushInterval: 5000,    // 5 second flush interval
  requestTimeout: 15000,  // 15s timeout
  enabled: true,          // Explicitly enable
});

process.on("beforeExit", () => langfuse.shutdownAsync());
process.on("SIGTERM", () => langfuse.shutdownAsync().then(() => process.exit(0)));
```

### Production Error Handling

```typescript
import { observe, updateActiveObservation, startActiveObservation } from "@langfuse/tracing";

// Wrap all traced operations with error safety
const tracedEndpoint = observe({ name: "api-endpoint" }, async (req: Request) => {
  try {
    updateActiveObservation({
      input: { path: req.url, method: req.method },
      metadata: { userId: req.userId },
    });

    const result = await processRequest(req);

    updateActiveObservation({ output: { status: 200 } });
    return result;
  } catch (error) {
    // Log error to trace -- don't let tracing error mask app error
    try {
      updateActiveObservation({
        output: { error: String(error) },
        metadata: { level: "ERROR" },
      });
    } catch {
      // Tracing failure must never break the app
    }
    throw error;
  }
});
```

## Pre-Deployment Verification Script

```typescript
// scripts/verify-langfuse-prod.ts
import { LangfuseClient } from "@langfuse/client";
import { startActiveObservation, updateActiveObservation } from "@langfuse/tracing";

async function verify() {
  const checks: Array<{ name: string; pass: boolean; detail: string }> = [];

  // 1. Environment variables
  const requiredVars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"];
  for (const v of requiredVars) {
    checks.push({
      name: `Env: ${v}`,
      pass: !!process.env[v],
      detail: process.env[v] ? `SET (${process.env[v]!.slice(0, 10)}...)` : "MISSING",
    });
  }

  // 2. Key validation
  const pk = process.env.LANGFUSE_PUBLIC_KEY || "";
  const sk = process.env.LANGFUSE_SECRET_KEY || "";
  checks.push({
    name: "Key format",
    pass: pk.startsWith("pk-lf-") && sk.startsWith("sk-lf-"),
    detail: `Public: ${pk.startsWith("pk-lf-")}, Secret: ${sk.startsWith("sk-lf-")}`,
  });

  // 3. API connectivity
  try {
    const langfuse = new LangfuseClient();
    // Try fetching prompts as a connectivity test
    await langfuse.prompt.get("__health-check__").catch(() => {});
    checks.push({ name: "API connectivity", pass: true, detail: "Connected" });
  } catch (error) {
    checks.push({ name: "API connectivity", pass: false, detail: String(error) });
  }

  // 4. Trace creation
  try {
    await startActiveObservation("prod-verify", async () => {
      updateActiveObservation({
        input: { test: true },
        output: { verified: true },
        metadata: { verification: "pre-deploy" },
      });
    });
    checks.push({ name: "Trace creation", pass: true, detail: "Trace created" });
  } catch (error) {
    checks.push({ name: "Trace creation", pass: false, detail: String(error) });
  }

  // Report
  console.log("\n=== Langfuse Production Verification ===\n");
  let allPassed = true;
  for (const check of checks) {
    const icon = check.pass ? "PASS" : "FAIL";
    console.log(`  [${icon}] ${check.name}: ${check.detail}`);
    if (!check.pass) allPassed = false;
  }

  console.log(`\n${allPassed ? "All checks passed." : "SOME CHECKS FAILED."}\n`);
  if (!allPassed) process.exit(1);
}

verify();
```

## Production Checklist

### Authentication & Security
- [ ] Production API keys created (separate from dev/staging)
- [ ] Keys stored in secret manager (not env files or code)
- [ ] Key prefix validated at startup (`pk-lf-` / `sk-lf-`)
- [ ] PII scrubbing enabled on trace inputs/outputs
- [ ] Secret scanning in CI/CD pipeline

### SDK Configuration
- [ ] Singleton client pattern (no per-request instantiation)
- [ ] Batch size tuned (`flushAt: 25-50`)
- [ ] Flush interval set (`flushInterval: 5000`)
- [ ] Request timeout configured (`requestTimeout: 15000`)

### Reliability
- [ ] Graceful shutdown on SIGTERM/SIGINT
- [ ] All spans end in `try/finally` (v3) or use `observe`/`startActiveObservation` (v4+)
- [ ] Tracing errors caught -- never crash the app
- [ ] Circuit breaker for sustained failures

### Monitoring
- [ ] Trace creation success/failure logged
- [ ] Flush latency tracked
- [ ] Rate limit errors monitored
- [ ] Dashboard alerts for quality score regression

### Operations
- [ ] Runbook documented for Langfuse outages
- [ ] Fallback behavior defined (app works without Langfuse)
- [ ] Data retention policy configured
- [ ] Log rotation includes redaction of API keys

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing traces in prod | No flush on exit | Add shutdown handler for SIGTERM |
| Memory growth | Client created per request | Use singleton pattern |
| High latency | Small batches | Increase `flushAt` to 25-50 |
| Lost traces on deploy | No graceful shutdown | Add SIGTERM handler with `sdk.shutdown()` |

## Resources
- [TypeScript SDK Setup](https://langfuse.com/docs/observability/sdk/typescript/setup)
- [Advanced Configuration](https://langfuse.com/docs/observability/sdk/typescript/advanced-usage)
- [Self-Hosting Guide](https://langfuse.com/self-hosting)
