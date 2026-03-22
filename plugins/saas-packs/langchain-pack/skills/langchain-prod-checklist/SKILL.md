---
name: langchain-prod-checklist
description: |
  Production readiness checklist for LangChain applications.
  Use when preparing for launch, validating deployment readiness,
  or auditing existing production LangChain systems.
  Trigger: "langchain production", "langchain prod ready",
  "deploy langchain", "langchain launch checklist", "go-live langchain".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, deployment, audit]

---
# LangChain Production Checklist

## Overview

Comprehensive go-live checklist for deploying LangChain applications to production. Covers configuration, resilience, observability, performance, security, testing, deployment, and cost management.

## 1. Configuration & Secrets

- [ ] All API keys in secrets manager (not `.env` in production)
- [ ] Environment-specific configs (dev/staging/prod) validated with Zod
- [ ] Startup validation fails fast on missing config
- [ ] `.env` files in `.gitignore`

```typescript
// Startup validation
import { z } from "zod";

const ProdConfig = z.object({
  OPENAI_API_KEY: z.string().startsWith("sk-"),
  LANGSMITH_API_KEY: z.string().startsWith("lsv2_"),
  NODE_ENV: z.literal("production"),
});

try {
  ProdConfig.parse(process.env);
} catch (e) {
  console.error("Invalid production config:", e);
  process.exit(1);
}
```

## 2. Error Handling & Resilience

- [ ] `maxRetries` configured on all models (3-5)
- [ ] `timeout` set on all models (30-60s)
- [ ] Fallback models configured with `.withFallbacks()`
- [ ] Error responses return safe messages (no stack traces to users)

```typescript
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  maxRetries: 5,
  timeout: 30000,
}).withFallbacks({
  fallbacks: [new ChatAnthropic({ model: "claude-sonnet-4-20250514" })],
});
```

## 3. Observability

- [ ] LangSmith tracing enabled (`LANGSMITH_TRACING=true`)
- [ ] `LANGCHAIN_CALLBACKS_BACKGROUND=true` (non-serverless only)
- [ ] Structured logging on all LLM/tool calls
- [ ] Prometheus metrics exported (requests, latency, tokens, errors)
- [ ] Alerting rules configured (error rate >5%, P95 latency >5s)

## 4. Performance

- [ ] Caching enabled for repeated queries (Redis or SQLite)
- [ ] `maxConcurrency` set on batch operations
- [ ] Streaming enabled for user-facing responses
- [ ] Connection pooling configured
- [ ] Prompt length optimized (no unnecessary verbosity)

## 5. Security

- [ ] User input isolated in human messages (never in system prompts)
- [ ] Input length limits enforced
- [ ] Prompt injection patterns logged/flagged
- [ ] Tools restricted to allowlisted operations
- [ ] LLM output validated before display (no PII/key leakage)
- [ ] Audit logging on all LLM and tool calls
- [ ] Rate limiting per user/IP

## 6. Testing

- [ ] Unit tests for all chains (using `FakeListChatModel`, no API calls)
- [ ] Integration tests with real LLMs (gated behind CI secrets)
- [ ] RAG pipeline validation (retrieval relevance + no hallucination)
- [ ] Tool unit tests (valid input, invalid input, error cases)
- [ ] Load testing completed (concurrent users, batch operations)

## 7. Deployment

- [ ] Health check endpoint returns LLM connectivity status
- [ ] Graceful shutdown handles in-flight requests
- [ ] Rolling deployment (zero downtime)
- [ ] Rollback procedure documented and tested
- [ ] Container resource limits set (memory, CPU)

```typescript
// Health check endpoint
app.get("/health", async (_req, res) => {
  const checks: Record<string, string> = { server: "ok" };

  try {
    await model.invoke("ping");
    checks.llm = "ok";
  } catch (e: any) {
    checks.llm = `error: ${e.message.slice(0, 100)}`;
  }

  const healthy = Object.values(checks).every((v) => v === "ok");
  res.status(healthy ? 200 : 503).json({ status: healthy ? "healthy" : "degraded", checks });
});

// Graceful shutdown
process.on("SIGTERM", async () => {
  console.log("Shutting down gracefully...");
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(1), 10000); // force after 10s
});
```

## 8. Cost Management

- [ ] Token usage tracking callback attached
- [ ] Daily/monthly budget limits enforced
- [ ] Model tiering: cheap model for simple tasks, powerful for complex
- [ ] Cost alerts configured (Slack/email on threshold)
- [ ] Cost per user/tenant tracked

## Pre-Launch Validation Script

```typescript
async function validateProduction() {
  const results: Record<string, string> = {};

  // 1. Config
  try {
    ProdConfig.parse(process.env);
    results["Config"] = "PASS";
  } catch { results["Config"] = "FAIL: missing env vars"; }

  // 2. LLM connectivity
  try {
    await model.invoke("ping");
    results["LLM"] = "PASS";
  } catch (e: any) { results["LLM"] = `FAIL: ${e.message.slice(0, 50)}`; }

  // 3. Fallback
  try {
    const fallbackModel = model.withFallbacks({ fallbacks: [fallback] });
    await fallbackModel.invoke("ping");
    results["Fallback"] = "PASS";
  } catch { results["Fallback"] = "FAIL"; }

  // 4. LangSmith
  results["LangSmith"] = process.env.LANGSMITH_TRACING === "true" ? "PASS" : "WARN: disabled";

  // 5. Health endpoint
  try {
    const res = await fetch("http://localhost:8000/health");
    results["Health"] = res.ok ? "PASS" : "FAIL";
  } catch { results["Health"] = "FAIL: not reachable"; }

  console.table(results);
  const allPass = Object.values(results).every((v) => v === "PASS");
  console.log(allPass ? "READY FOR PRODUCTION" : "ISSUES FOUND - FIX BEFORE LAUNCH");
  return allPass;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| API key missing at startup | Secrets not mounted | Check deployment config |
| No fallback on outage | `.withFallbacks()` not configured | Add fallback model |
| LangSmith trace gaps | Background callbacks in serverless | Set `LANGCHAIN_CALLBACKS_BACKGROUND=false` |
| Cache miss storm | Redis down | Implement graceful degradation |

## Resources

- [LangChain Production Guide](https://js.langchain.com/docs/how_to/production/)
- [LangSmith Production Tracing](https://docs.smith.langchain.com/)
- [Twelve-Factor App](https://12factor.net/)

## Next Steps

After launch, use `langchain-observability` for monitoring and `langchain-incident-runbook` for incident response.
