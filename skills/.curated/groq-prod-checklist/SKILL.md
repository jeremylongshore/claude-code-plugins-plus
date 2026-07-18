---
name: groq-prod-checklist
description: 'Execute Groq production deployment checklist and go-live procedures.

  Use when deploying Groq integrations to production, preparing for launch,

  or implementing go-live procedures.

  Trigger with phrases like "groq production", "deploy groq",

  "groq go-live", "groq launch checklist".

  '
allowed-tools: Read, Bash(curl:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- deployment
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Production Checklist

## Overview

Complete pre-launch checklist for deploying Groq-powered applications to production. Covers API key security, model selection, rate limit planning, fallback strategies, and monitoring setup. Work top-to-bottom: each section is a gate that must be green before the go-live verification runs.

Deep code (fallback function, health-check endpoint, go-live script) lives in `references/` so this file stays scannable — drill in when you reach that step.

## Prerequisites

- Staging environment tested with Groq API
- Groq Developer or Enterprise plan (free tier is not suitable for production)
- Production API key created in console.groq.com
- Monitoring and alerting infrastructure ready

## Instructions

Read the target app's Groq integration and config, then walk each gate below. Tick every box; an unchecked item is a launch blocker.

### 1. API Key & Auth

- [ ] Production API key stored in secret manager (not `.env` files)
- [ ] Key is NOT shared with development or staging environments
- [ ] Key rotation procedure documented and tested
- [ ] Pre-commit hook blocks `gsk_` pattern in code

### 2. Model Selection

- [ ] Production model chosen and tested (recommend `llama-3.3-70b-versatile`)
- [ ] Fallback model configured (`llama-3.1-8b-instant`)
- [ ] Deprecated model IDs removed (check [deprecations](https://console.groq.com/docs/deprecations))
- [ ] `max_tokens` set to actual expected output size (not context max)

### 3. Rate Limit Planning

- [ ] Production rate limits known (check console.groq.com/settings/limits)
- [ ] Estimated peak RPM < 80% of limit
- [ ] Estimated peak TPM < 80% of limit
- [ ] Exponential backoff with `retry-after` header implemented
- [ ] Request queue for burst protection (`p-queue` or similar)

### 4. Error Handling & Fallback

- [ ] All Groq error types caught (`Groq.APIError`, `Groq.APIConnectionError`)
- [ ] 429 errors retried with backoff
- [ ] 5xx errors retried with backoff
- [ ] 401 errors trigger alert (key may be revoked)
- [ ] Network timeouts configured (default 60s may be too long)
- [ ] Circuit breaker pattern for sustained failures
- [ ] Fallback-to-degradation wrapper in place — see the `completionWithFallback` pattern in [references/implementation.md](references/implementation.md)

### 5. Health Check

- [ ] `/api/health` (or `/healthz`) probes Groq with a 1-token request and returns `503` when degraded — full route in [references/implementation.md](references/implementation.md)

### 6. Monitoring Setup

- [ ] Latency histogram (p50, p95, p99)
- [ ] Token throughput counter (tokens/sec by model)
- [ ] Error rate by status code (429, 5xx)
- [ ] Rate limit remaining gauge (from response headers)
- [ ] Cost tracking (tokens * price per million)
- [ ] Alert: latency p95 > 1s (Groq normally < 200ms)
- [ ] Alert: error rate > 5%
- [ ] Alert: rate limit remaining < 10%

### 7. Spending Controls

- [ ] Monthly spending cap set in Groq Console
- [ ] Budget alerts at 50%, 80%, 95%
- [ ] Auto-pause enabled when cap is reached

### 8. Documentation

- [ ] Incident runbook created (see `groq-incident-runbook`)
- [ ] Key rotation SOP documented
- [ ] On-call knows how to check [status.groq.com](https://status.groq.com)
- [ ] Rollback procedure tested

### 9. Go-Live Verification

Run the pre-flight `curl` script against production — status, key, health endpoint, and rate-limit headroom must all pass. Full script and pass/fail table in [references/go-live.md](references/go-live.md).

## Output

Working through this skill produces a **go / no-go launch decision**:

- A completed checklist where every box is ticked or explicitly waived with a reason.
- A green go-live verification run (all four pre-flight checks passing).
- The alert matrix (below) wired into your monitoring stack.

Any unchecked security or auth item (Sections 1, 2) is a hard blocker; unchecked monitoring or spending items (Sections 6, 7) are P3 blockers that may launch with a tracked follow-up.

## Error Handling

Wire these alerts before go-live so production failures page the right severity:

| Alert | Condition | Severity |
|-------|-----------|----------|
| API errors spike | 5xx rate > 5/min | P1 |
| Latency degraded | p95 > 1000ms | P2 |
| Rate limited | 429 count > 5/min | P2 |
| Auth failure | Any 401 error | P1 |
| Spending near cap | >90% of monthly budget | P3 |

## Examples

Minimal fallback skeleton — try the primary model, fall back to the fast model on 429/5xx:

```typescript
try {
  return await groq.chat.completions.create({ model: "llama-3.3-70b-versatile", messages, timeout: 15_000 });
} catch (err: any) {
  if (err.status === 429 || err.status >= 500) {
    return await groq.chat.completions.create({ model: "llama-3.1-8b-instant", messages, timeout: 10_000 });
  }
  throw err;
}
```

- Full fallback-with-degradation function and health-check endpoint: [references/implementation.md](references/implementation.md)
- Complete go-live verification script and result interpretation: [references/go-live.md](references/go-live.md)

## Resources

- [Groq Status Page](https://status.groq.com)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)
- [Groq Models (check deprecations)](https://console.groq.com/docs/deprecations)

## Next Steps

Once launched, keep the integration current: schedule model-deprecation reviews against the Groq deprecations page, and for version upgrades follow the `groq-upgrade-migration` skill. If an incident fires an alert above, escalate through the `groq-incident-runbook`.
