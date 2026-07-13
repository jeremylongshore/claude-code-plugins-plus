---
name: openrouter-prod-checklist
description: 'Validate production readiness of your OpenRouter integration. Use before
  launching to production or during operational reviews. Triggers: ''openrouter production'',
  ''openrouter launch'', ''production checklist openrouter'', ''openrouter deploy''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(curl:*), Bash(jq:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- production
- deployment
- checklist
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Production Checklist

## Overview

A comprehensive production readiness checklist for OpenRouter integrations covering security, reliability, observability, cost management, and operational procedures. Each item includes the specific API endpoint or configuration needed to verify compliance.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- A working OpenRouter integration ready to launch — this skill validates an existing integration, it doesn't build one
- `curl` and `jq` for the pre-launch validation script and the auth/credit-limit checks
- Python 3.8+ if you turn the checklist dicts (`SECURITY`, `RELIABILITY`, `OBSERVABILITY`) into automated CI checks
- A secret scanner in CI (gitleaks or trufflehog) — the security checklist verifies its presence

## Instructions

1. Work through the Security Checklist: keys in a secrets manager, 90-day rotation, per-key credit limits (`GET /api/v1/auth/key` → `.data.limit`), secret scanning in CI, HTTPS-only endpoints.
2. Verify the Reliability Checklist: a fallback chain (`models` array + `route: "fallback"`), SDK `max_retries=3` with built-in backoff, `timeout=30.0`, a circuit breaker on the primary model, and `max_tokens` on every request.
3. Confirm the Observability Checklist: structured logs carrying `generation_id`/model/latency/tokens/cost, error-rate alerts (>5% over 5 min), P50/P95 latency per model, daily cost tracking via `GET /api/v1/generation?id=`, and credit-balance alerts.
4. Run the Pre-Launch Validation Script — it exercises auth, credit limit, primary-model availability, a live test request, and a hardcoded-key scan.
5. Fix every FAIL and re-run until the script prints `READY FOR PRODUCTION`, then wire it into CI as a pre-deploy gate per Enterprise Considerations.

## Security Checklist

```python
SECURITY = {
    "api_key_storage": {
        "check": "API keys stored in secrets manager (not .env files on disk)",
        "verify": "grep -r 'sk-or-v1-' --include='*.py' --include='*.ts' . | grep -v node_modules",
        "pass": "Zero matches",
    },
    "key_rotation": {
        "check": "Keys rotated on 90-day schedule",
        "verify": "Check key creation dates in OpenRouter dashboard",
        "api": "GET /api/v1/keys (management key)",
    },
    "credit_limits": {
        "check": "Per-key credit limits set to isolate blast radius",
        "verify": "curl -s https://openrouter.ai/api/v1/auth/key -H 'Authorization: Bearer $KEY' | jq '.data.limit'",
        "pass": "Non-null limit value",
    },
    "secret_scanning": {
        "check": "CI pipeline includes secret scanning (gitleaks, trufflehog)",
        "verify": "Check CI config for secret scanning step",
    },
    "https_enforced": {
        "check": "All requests use https://openrouter.ai/api/v1",
        "verify": "Grep codebase for 'http://openrouter' (should be zero)",
    },
}
```

## Reliability Checklist

```python
RELIABILITY = {
    "fallback_models": {
        "check": "Fallback chain configured for critical models",
        "config": """extra_body={"models": ["primary", "secondary", "tertiary"], "route": "fallback"}""",
    },
    "retry_logic": {
        "check": "Retry with exponential backoff for 429 and 5xx errors",
        "config": "OpenAI SDK max_retries=3 (built-in backoff)",
    },
    "timeouts": {
        "check": "Per-request timeout configured",
        "config": "OpenAI(timeout=30.0)  # 30s per request",
    },
    "circuit_breaker": {
        "check": "Circuit breaker on primary model (3 failures → fallback)",
        "verify": "Review client wrapper for circuit breaker pattern",
    },
    "max_tokens": {
        "check": "max_tokens set on EVERY request",
        "verify": "Grep codebase for .create( calls without max_tokens",
    },
}
```

## Observability Checklist

```python
OBSERVABILITY = {
    "structured_logging": {
        "check": "Every API call logged with generation_id, model, latency, tokens, cost",
        "fields": ["timestamp", "generation_id", "model", "latency_ms", "prompt_tokens",
                   "completion_tokens", "cost", "status", "user_id"],
    },
    "error_alerting": {
        "check": "Alerts on error rate spikes (>5% over 5 min window)",
        "metric": "count(status=error) / count(*) over sliding 5min window",
    },
    "latency_monitoring": {
        "check": "P50 and P95 latency tracked per model",
        "threshold": "P95 < 10s for standard models, P95 < 30s for reasoning models",
    },
    "cost_tracking": {
        "check": "Daily cost tracked and compared to budget",
        "api": "GET /api/v1/generation?id={gen_id} for exact per-request cost",
    },
    "credit_balance_alert": {
        "check": "Alert when credits drop below threshold",
        "api": "GET /api/v1/auth/key → .data.usage vs .data.limit",
    },
}
```

## Pre-Launch Validation Script

```bash
#!/bin/bash
echo "=== OpenRouter Production Readiness ==="
PASS=0; FAIL=0

# 1. Auth works
echo -n "1. API Authentication: "
AUTH=$(curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq -r '.data.label // "FAIL"')
if [ "$AUTH" != "FAIL" ]; then echo "PASS ($AUTH)"; ((PASS++)); else echo "FAIL"; ((FAIL++)); fi

# 2. Credit limit set
echo -n "2. Credit Limit: "
LIMIT=$(curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq -r '.data.limit // "NONE"')
if [ "$LIMIT" != "NONE" ] && [ "$LIMIT" != "null" ]; then
  echo "PASS (\$$LIMIT)"; ((PASS++))
else echo "WARN (no limit set)"; ((FAIL++)); fi

# 3. Primary model available
echo -n "3. Primary Model Available: "
MODEL="anthropic/claude-3.5-sonnet"
EXISTS=$(curl -s https://openrouter.ai/api/v1/models | jq --arg m "$MODEL" '[.data[] | select(.id == $m)] | length')
if [ "$EXISTS" -gt 0 ]; then echo "PASS ($MODEL)"; ((PASS++)); else echo "FAIL"; ((FAIL++)); fi

# 4. Test request succeeds
echo -n "4. Test Request: "
TEST=$(curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  | jq -r '.choices[0].message.content // "FAIL"')
if [ "$TEST" != "FAIL" ]; then echo "PASS"; ((PASS++)); else echo "FAIL"; ((FAIL++)); fi

# 5. No hardcoded keys
echo -n "5. No Hardcoded Keys: "
KEYS=$(grep -r "sk-or-v1-" --include="*.py" --include="*.ts" --include="*.js" . 2>/dev/null | grep -v node_modules | grep -v ".env" | wc -l)
if [ "$KEYS" -eq 0 ]; then echo "PASS"; ((PASS++)); else echo "FAIL ($KEYS found)"; ((FAIL++)); fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "READY FOR PRODUCTION" || echo "FIX FAILURES BEFORE LAUNCH"
```

## Output

- A pass/fail pre-launch validation report: five numbered checks, a `Results: N passed, M failed` summary, and a final `READY FOR PRODUCTION` / `FIX FAILURES BEFORE LAUNCH` verdict
- A completed three-part readiness checklist (security, reliability, observability) with the verify command or API endpoint recorded per item
- A hardcoded-key scan result — zero `sk-or-v1-` matches in source outside `.env` and `node_modules`

## Examples

A correctly configured production key produces a clean run of the Pre-Launch Validation Script:

```text
=== OpenRouter Production Readiness ===
1. API Authentication: PASS (my-app-prod)
2. Credit Limit: PASS ($100)
3. Primary Model Available: PASS (anthropic/claude-3.5-sonnet)
4. Test Request: PASS
5. No Hardcoded Keys: PASS

Results: 5 passed, 0 failed
READY FOR PRODUCTION
```

A key with no credit limit instead shows `WARN (no limit set)` on check 2 and counts as a failure — set a per-key limit to bound blast radius before launch. More worked examples: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Production key exposed | Key logged or committed | Rotate immediately; deploy from secrets manager |
| No fallback configured | Primary model goes down | Add `models` array with `route: "fallback"` |
| Missing monitoring | Errors go undetected | Set up alerting before launch |
| No max_tokens | Runaway completion costs | Add max_tokens to every request |

## Enterprise Considerations

- Run the validation script in CI as a pre-deploy gate
- Set up runbooks for common failure scenarios: rate limiting, credit exhaustion, provider outage
- Load test at 2x expected peak traffic to validate rate limits and fallback behavior
- Document escalation paths: when to contact OpenRouter support vs handle internally
- Review and update this checklist quarterly as OpenRouter adds features
- Keep a "break glass" procedure for emergency key rotation

## References

- Examples | Errors
- [API Reference](https://openrouter.ai/docs/api/reference/overview) | [Status](https://status.openrouter.ai)
