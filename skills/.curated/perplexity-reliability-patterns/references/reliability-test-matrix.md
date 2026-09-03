# Reliability Verification Matrix

Exercise these cases with deterministic fakes before enabling a fallback or retry policy in production. Assertions must cover observable behavior, not merely that the function returned.

| Case | Expected behavior | Forbidden behavior |
|---|---|---|
| Valid response | Return parsed answer and citations within deadline | Accept malformed required fields |
| HTTP 400/422 | Return validation failure immediately | Retry or switch models |
| HTTP 401/403 | Surface credential or authorization failure | Serve cached success or print key metadata |
| HTTP 402 | Surface billing failure | Retry another model |
| HTTP 429 | Honor bounded delay and attempt ceiling | Start parallel retries or sleep without cancellation |
| HTTP 500/503 | Count breaker failure; use compatible fallback | Replay non-idempotent work blindly |
| Connect/read timeout | Abort the in-flight request | Leave a stream or socket running |
| Stalled stream | Abort before the next chunk deadline | Check timeout only after a late chunk arrives |
| Open circuit | Skip provider call during cool-down | Probe on every request |
| Half-open circuit | Permit one controlled probe | Release a traffic surge |
| Cache fallback | Return only same-tenant, explicitly cacheable data labeled stale | Cross tenant or retention boundary |
| Unsafe citation scheme | Reject before render | Fetch or navigate server-side |
| Local/IP citation host | Reject before render | Resolve or follow redirects |
| Unapproved citation host | Reject or isolate | Treat model output as an allowlist decision |

## Test invariants

- Use fake clocks for retry, breaker, cache TTL, and stream-deadline tests.
- Use deterministic jitter or inject a delay function.
- Assert total attempts and elapsed budget.
- Assert the abort signal reaches the active request or iterator.
- Seed cache entries for two tenants and prove isolation in both directions.
- Include `javascript:`, `data:`, userinfo, localhost, IPv4, IPv6, and deceptive subdomain citations.
- Assert logs contain no prompt, answer, raw URL, API-key fragment, or raw provider body.

## Rollout evidence

Record baseline and canary error rate, p50/p95/p99 latency, retry amplification, fallback rate, circuit state transitions, cache age, and user-visible degradation. Establish rollback thresholds before rollout; do not invent them during an incident.

## Primary references

- [Perplexity SDK error handling](https://docs.perplexity.ai/docs/sdk/error-handling)
- [Perplexity SDK configuration](https://docs.perplexity.ai/docs/sdk/configuration)
- [Sonar response structure](https://docs.perplexity.ai/docs/sonar/openai-compatibility)
