---
name: orcarouter-fallback-reliability
description: |
  Make OrcaRouter calls resilient with fallback and retry patterns. Use when a
  primary model is down or rate-limited, when you need an automatic fallback
  chain, or when you are hardening a production LLM path. Triggers:
  "orcarouter fallback", "orcarouter failover", "orcarouter retry",
  "resilience", "reliability", "circuit breaker".
  Trigger with "orcarouter-fallback-reliability" keywords like "orcarouter", "gateway", or the skill name.
allowed-tools: Bash(curl:*), Bash(grep:*), Bash(python3:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Kus Wardhanie <kuswardhanietidims-svg@users.noreply.github.com>
tags:
- saas
- orcarouter
- reliability
- fallback
- failover
- production
compatibility: Designed for Claude Code
---
# OrcaRouter Fallback & Reliability

## Overview

Build resilience into OrcaRouter calls. The gateway supports **server-side fallback chains** via `extra_body.models` + `route: "fallback"` — if the primary model fails (5xx / 429 / network error), the gateway tries the next entry before returning. On top of that you layer client-side retries with backoff for the cases the gateway cannot absorb (a chain that exhausted every entry, a transient 5xx/429 the gateway surfaced to you).

Retries are **fail-closed**: only network failures, `408`, `429`, and `5xx` are retried. Auth, malformed-request, policy-denial, guardrail, and approval-pending responses never retry — they are deterministic, and looping on them burns quota without changing the outcome. This skill covers both layers.

## Prerequisites

- An OrcaRouter API key (`sk-orca-...`) exported as `ORCAROUTER_API_KEY`
- Python 3.8+ / Node.js 18+ with the OpenAI SDK, or cURL + jq
- At least two model IDs you can call (see `orcarouter-model-routing`)

## Instructions

1. Start with a server-side fallback chain (`extra_body.models` + `route: "fallback"`) for upstream failures.
2. Add client-side retries with exponential backoff for `429` and transient `5xx` — and only for those, plus network failures and `408`.
3. Fail closed on everything else: `400`, `401`, `402`, `403`, `404`, `422`, and the gateway policy blocks (`guardrail_blocked` / `firewall_blocked` / `firewall_approval_pending`). These are deterministic — re-raise instead of retrying.
4. Log the served model from the `X-Orca-Fallback-Model` header to verify the chain.

## Server-Side Fallback Chain

The gateway tries the chain in order. The top-level `model` is the first attempt; when the chain is present the gateway uses it. Max 5 models; same endpoint type recommended (e.g. all chat models). Billing is for the model that actually served.

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

r = client.chat.completions.create(
    model="anthropic/claude-sonnet-4.6",   # primary
    messages=[{"role": "user", "content": "Critical task"}],
    max_tokens=200,
    extra_body={
        "models": [
            "anthropic/claude-sonnet-4.6",
            "openai/gpt-4o-mini",
            "google/gemini-2.5-flash",
        ],
        "route": "fallback",
    },
)
```

The response headers `X-Orca-Fallback-Level` (0 = primary served) and `X-Orca-Fallback-Model` name the model that served the request. See [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks).

```bash
curl -si https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-sonnet-4.6",
    "messages": [{"role": "user", "content": "Critical task"}],
    "max_tokens": 200,
    "extra_body": {
      "models": ["anthropic/claude-sonnet-4.6", "openai/gpt-4o-mini", "google/gemini-2.5-flash"],
      "route": "fallback"
    }
  }' | grep -iE '^x-orca-fallback|content'
```

## Client-Side Retry with Backoff

Only three classes of failure are worth retrying:

| Class | Examples | Retry? |
| ----- | -------- | ------ |
| Transport | connection error, timeout, DNS/socket failure | Yes — no HTTP status was produced |
| Rate limit | `408` (request timeout), `429` (rate limit / credit constraint) | Yes — honor `Retry-After` |
| Server | `500`, `502`, `503`, `504` | Yes — transient upstream failure |

Everything else fails closed. `401`/`403` (auth), `400`/`422` (malformed request), `402` (insufficient credits), `404` (unknown model/route), and the policy blocks (`guardrail_blocked`, `firewall_blocked`, `firewall_approval_pending`) are deterministic: retrying sends the identical request to the identical verdict. Re-raise them.

The classifier below is explicit about both directions — it retries an allow-list of transient failures and re-raises everything else, including exception types it does not recognize:

```python
from openai import OpenAI, APIConnectionError, APITimeoutError, APIStatusError
import os, time, random

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
    max_retries=0,  # we manage retries ourselves below
)

RETRYABLE_STATUS = {408, 429}                                # + any 5xx
POLICY_CODES = {"guardrail_blocked", "firewall_blocked",  # deterministic, skip-retry
                "firewall_approval_pending"}

def _error_code(e):
    body = getattr(e, "body", None)
    err = body.get("error") if isinstance(body, dict) else None
    return err.get("code") if isinstance(err, dict) else None

def _retry_after(e):
    """Seconds to wait, or None when the header is absent/non-numeric."""
    resp = getattr(e, "response", None)
    raw = resp.headers.get("retry-after") if resp is not None else None
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return None  # absent or HTTP-date form -> fall back to exponential backoff

def _is_retryable(e):
    if isinstance(e, (APIConnectionError, APITimeoutError)):   # transport: no status
        return True
    if isinstance(e, APIStatusError):
        if _error_code(e) in POLICY_CODES:
            return False                                       # policy block: fail closed
        return e.status_code in RETRYABLE_STATUS or 500 <= e.status_code < 600
    return False                                               # unknown type: fail closed

def call_with_retry(**kwargs):
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            if not _is_retryable(e) or attempt == max_attempts - 1:
                raise                                        # fail closed: no retry, or out of attempts
            wait = _retry_after(e)
            if wait is None:
                wait = min(60.0, 2 ** attempt + random.uniform(0, 0.5))  # 1s, 2s, 4s + jitter
            print(f"retry in {wait:.1f}s after: {type(e).__name__}")
            time.sleep(wait)

r = call_with_retry(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)
```

A retry that raised `400 guardrail_blocked` or `401` propagates immediately — the caller sees the real error on the first attempt instead of after four identical sends. The broad `except Exception` here is safe only because `_is_retryable` gates it; do not drop that guard, and do not replace the classifier with a bare "retry on any exception".

## What Not to Retry

- **`401` / `403`** — invalid or restricted key; fix the credential/scope and fail fast
- **`400` / `422`** — malformed request; retrying wastes quota
- **`402`** — insufficient credits; top up or switch to a cheaper routing tier
- **`404`** — unknown model or route; check `/v1/models`
- **`guardrail_blocked` / `firewall_blocked` / `firewall_approval_pending`** — deterministic policy blocks marked skip-retry; change the input or resolve the approval instead (see `orcarouter-agent-security`)
- **Anything not on the retryable allow-list**, including exception types the classifier does not recognize
- **A `429` that repeats identically after backoff** — on the free tier this means the prompt exceeded the per-request cap; shrink or restructure the request rather than looping unchanged

## Output

A resilient call path returns a completion. When the primary route fails, the gateway (server-side chain) or your client retry loop handles it, and the response headers tell you which model served. Transient `429`/`5xx` and transport failures become handled delays instead of raised exceptions; everything deterministic propagates to the caller unchanged.

## Examples

```text
# Server-side chain fell back after the primary 5xx'd:
x-orca-fallback-level: 1
x-orca-fallback-model: openai/gpt-4o-mini

# Client retry honored Retry-After on a 429, then succeeded:
retry in 2.0s after: RateLimitError

# Fail-closed paths — these raise on the first attempt, no retry:
HTTP 401                          -> AuthenticationError (no delay, no second attempt)
HTTP 400 {"error": {"code": "guardrail_blocked"}}  -> raised as-is
HTTP 402                          -> raised as-is
```

More reliability patterns (circuit breaker, idempotency, timeout budgets): `references/reliability-patterns.md`.

## Error Handling

| HTTP | Cause | Client response |
|------|-------|-----------------|
| 408 | Request timeout at the gateway | Retry after `Retry-After`, then exponential backoff |
| 429 | Rate limit or credit constraint | Honor `Retry-After`, retry; then exponential backoff |
| 5xx | Upstream provider failure | Server-side fallback chain handles most; client retry handles the rest |
| 400 | Malformed request, or a policy block | Do not retry; branch on `error.code` for policy blocks |
| 401 | Invalid key | Do not retry — fail fast with a config error |
| 402 | Insufficient credits | Do not retry — top up or change routing tier |
| 403 | Key restricted (scope/IP/model allowlist) | Do not retry — change model or key settings |
| 404 | Unknown model or route | Do not retry — check `/v1/models` |
| 422 | Unprocessable request body | Do not retry — fix the request |

## Enterprise Considerations

- Retry only the allow-list (network, `408`, `429`, `5xx`); a bare `except Exception` that retries everything turns a deterministic denial into wasted quota and a delayed error
- Set a timeout budget per call; total chain latency = sum of attempts
- Log `X-Orca-Fallback-Model` on every hop for audit and cost control
- Combine server-side fallback chains with client retries for the strongest path

## References

- Circuit breaker and timeout patterns: `references/reliability-patterns.md`
- [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks) · [Rate Limits](https://docs.orcarouter.ai/operations/rate-limits) · [Error codes](https://docs.orcarouter.ai/security/reference/error-codes) · [Free Models](https://docs.orcarouter.ai/routing/free-models)
