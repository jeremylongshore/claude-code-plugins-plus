---
name: elevenlabs-prod-checklist
description: |
  Execute an ElevenLabs production deployment checklist with health checks and rollback.
  Use when deploying TTS/voice integrations to production, preparing for launch, or
  implementing go-live procedures for ElevenLabs-powered apps.
  Trigger with "elevenlabs production", "deploy elevenlabs", "elevenlabs go-live",
  "elevenlabs launch checklist", or "production TTS".
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- production
- deployment
compatibility: Designed for Claude Code
---
# ElevenLabs Production Checklist

## Overview

Complete checklist for deploying ElevenLabs TTS/voice integrations to production. Covers
API configuration, health checks, circuit breakers, monitoring, and rollback procedures.
The deep code for the resilience primitives lives in `references/` so this file stays a
fast, scannable runbook — drill in when you need the full implementation.

## Prerequisites

- Staging environment tested and verified
- Production API key (separate from dev/staging)
- Monitoring and alerting infrastructure ready

## Instructions

### Step 1: Pre-Deployment Verification

Walk the checklist below. Every unchecked box is a launch blocker.

**Configuration:**

- [ ] Production API key stored in secure vault (not in code)
- [ ] `ELEVENLABS_API_KEY` set in deployment platform's secrets
- [ ] Webhook secret configured (if using webhooks)
- [ ] Using production model ID (`eleven_multilingual_v2` or `eleven_v3`)

**Code Quality:**

- [ ] All tests passing with mocked ElevenLabs SDK
- [ ] No hardcoded API keys (scan with `grep -r "sk_" src/`)
- [ ] Error handling covers 400, 401, 404, 429, 5xx responses
- [ ] Rate limiting implemented matching plan concurrency limit
- [ ] Text splitting handles inputs > 5,000 characters
- [ ] Audio output format appropriate for use case

**Quota Planning:**

- [ ] Estimated monthly character usage fits within plan limit
- [ ] Usage-based billing enabled (Creator+ plans) if needed
- [ ] Flash/Turbo models used where latency matters more than quality

### Step 2: Wire the resilience primitives

Production ElevenLabs integrations need three primitives. The full drop-in TypeScript for
each is in [references/implementation.md](references/implementation.md) — high-level intent:

1. **Health check endpoint** — reports connectivity, latency, and remaining quota; returns
   `degraded` past 90% quota and `unhealthy` on any API failure, so a load balancer can gate
   traffic.
2. **Circuit breaker** — opens after N consecutive failures, cools down, then probes
   half-open; accepts a `fallback` (placeholder audio / cached clip / `null`) so a TTS outage
   degrades gracefully instead of throwing.
3. **Monitoring & alerting** — emit one structured metric per TTS call and drive the alert
   thresholds in the table below into your observability platform.

### Step 3: Run the pre-flight gate

Before promoting a build, run the pre-flight script — it checks connectivity, quota, voice
availability, and a live TTS smoke test, exiting non-zero on any hard failure so it can block
a CI/CD deploy step. Full script + CI wiring: [references/preflight.md](references/preflight.md).

```bash
# The load-bearing first gate — full script in references/preflight.md
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}")
[ "$HTTP" != "200" ] && echo "FAIL: API not reachable" && exit 1
```

## Output

Running this checklist produces:

- A completed pre-deployment verification (every box in Step 1 checked or explicitly waived).
- A health-check endpoint returning `healthy` / `degraded` / `unhealthy` plus latency and
  remaining quota.
- A circuit breaker and monitoring harness wired into the TTS call path.
- A green pre-flight run (`=== All checks passed ===`, exit 0) gating the deploy.
- A monitoring/alerting matrix mapped to your on-call severities (see below).

## Deployment Monitoring

| Alert | Condition | Severity |
|-------|-----------|----------|
| API unreachable | Health check fails 3x | P1 — Critical |
| Quota exhausted | 401 `quota_exceeded` | P1 — Critical |
| High error rate | 5xx > 5% of requests | P2 — High |
| Rate limited | 429 > 10/min sustained | P2 — High |
| High latency | p99 > 5000ms | P3 — Medium |
| Quota warning | > 80% used | P3 — Medium |

## Error Handling

| Scenario | Response |
|----------|----------|
| ElevenLabs API down | Circuit breaker opens; fallback to cached/placeholder audio |
| Quota exhausted mid-day | Alert team; switch to Flash model (0.5x cost); queue non-urgent requests |
| Voice deleted | Return 404 to caller; alert; fall back to default voice |
| Webhook delivery failing | Monitor ElevenLabs webhook health; webhooks auto-disable after 10 failures |

## Examples

**Gate a deploy on the pre-flight script.** Run it as the last step before promotion; a
non-zero exit blocks the pipeline:

```bash
$ ELEVENLABS_API_KEY=$PROD_KEY ./scripts/pre-flight-check.sh
=== ElevenLabs Pre-Flight Check ===
API connectivity: HTTP 200
Characters remaining: 428193
Voices available: 14
TTS smoke test: HTTP 200
=== All checks passed ===
$ echo $?
0
```

**Poll the health endpoint for a load-balancer probe.** A `degraded` status (quota > 90%)
still serves traffic but pages on-call; `unhealthy` drains the node:

```bash
$ curl -s https://myapp.example.com/health | jq '.status, .elevenlabs.quotaPctUsed'
"healthy"
41
```

Full worked implementations for both: [references/implementation.md](references/implementation.md)
and [references/preflight.md](references/preflight.md).

## Resources

- [ElevenLabs Status](https://status.elevenlabs.io)
- [ElevenLabs API Reference](https://elevenlabs.io/docs/api-reference/introduction)
- [Usage Dashboard](https://elevenlabs.io/app/usage)
- [references/implementation.md](references/implementation.md) — health check, circuit breaker, monitoring code
- [references/preflight.md](references/preflight.md) — pre-flight script + CI wiring

## Next Steps

For version upgrades, see `elevenlabs-upgrade-migration`. For cost optimization, see `elevenlabs-cost-tuning`.
