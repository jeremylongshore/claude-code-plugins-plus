# Provider Outage Playbook — Detect, Circuit-Break, Fail Over, Communicate

Provider outages (Anthropic, OpenAI, Azure OpenAI) are the easiest LLM
incidents to handle **if** you prepared failover ahead of time, and the
hardest to handle if you did not. This playbook assumes
`.with_fallbacks(backup)` is already wired (see `langchain-rate-limits`) —
during the incident, the work is detection, confirmation, and comms.

## Detection — three signals must agree

Do not declare a provider outage on one signal. Provider-side error rates
look similar to your app's bugs, your canary looks similar to a deploy issue,
and vendor status pages lag real incidents by 10–30 minutes.

### Signal 1: vendor status page watcher

Poll each provider's status page every 30s, surface into a Slack channel:

```python
import httpx

PROVIDERS = {
    "anthropic": "https://status.anthropic.com/api/v2/status.json",
    "openai": "https://status.openai.com/api/v2/status.json",
}

async def watch_status():
    async with httpx.AsyncClient(timeout=5) as client:
        for name, url in PROVIDERS.items():
            try:
                r = await client.get(url)
                indicator = r.json()["status"]["indicator"]
                if indicator != "none":
                    await slack_post(
                        f"Provider {name} status: {indicator}",
                        channel="#llm-oncall",
                    )
            except Exception as e:
                logger.warning(f"status check failed: {name}: {e}")
```

Run on a cron (every 30–60s). The `indicator` values are `none`, `minor`,
`major`, `critical`.

### Signal 2: in-app canary probe

A 1-req/min call to each configured provider with a trivial prompt. This
catches outages the vendor has not posted yet (early-incident gap), and
catches "working for them, broken for you" cases (network, auth, region).

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

CANARIES = {
    "anthropic": ChatAnthropic(model="claude-haiku-4-5", timeout=10, max_retries=0),
    "openai": ChatOpenAI(model="gpt-4o-mini", timeout=10, max_retries=0),
}

async def run_canaries():
    for name, llm in CANARIES.items():
        start = time.monotonic()
        try:
            await llm.ainvoke("say ok")
            status = "ok"
        except Exception as e:
            status = f"fail:{type(e).__name__}"
        dur = time.monotonic() - start
        canary_latency.labels(provider=name).observe(dur)
        canary_status.labels(provider=name, status=status).inc()
```

`max_retries=0` is deliberate — the canary should fail fast, not mask the
outage with retries.

### Signal 3: app-side error-rate spike on the primary

From your own metrics: `rate(langchain_requests_total{provider="anthropic", status="error"}[5m])`.
If this jumps but the canary is green and the status page is green, it is
your app's bug, not an outage.

### Confirmation matrix

| Status page | Canary | App errors | Verdict |
|---|---|---|---|
| Red | Fail | Spiking | Confirmed outage — fail over |
| Green | Fail | Spiking | Likely outage (vendor lag) — fail over, watch status page |
| Red | Pass | Baseline | Status page lag on a past incident — do not fail over |
| Green | Pass | Spiking | Your app's bug — do not fail over, debug |
| Green | Pass | Baseline | Healthy |

## Circuit breaker

Bounds the latency cost of a dead provider. After N consecutive failures in a
window, the breaker opens — new requests bypass the primary and go straight
to the fallback. After a timeout, the breaker half-opens for one probe; if it
passes, close, else stay open.

Minimal implementation with `aiobreaker`:

```python
from aiobreaker import CircuitBreaker
from datetime import timedelta
from langchain_core.runnables import RunnableLambda
from anthropic import APIError, APITimeoutError, RateLimitError

breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=timedelta(seconds=30),
)

async def breaker_call(llm, msg):
    return await breaker.call_async(llm.ainvoke, msg)

primary_with_breaker = RunnableLambda(lambda x: breaker_call(primary_llm, x))
resilient = primary_with_breaker.with_fallbacks(
    [backup_llm],
    exceptions_to_handle=(RateLimitError, APIError, APITimeoutError),
)
```

Tune `fail_max` high enough to absorb a single bad request (5 is reasonable);
`timeout_duration` low enough to probe recovery quickly (30s for critical
services, 2min for background jobs).

## Failover — one flip, not a code change

If `.with_fallbacks(backup)` is already wired, the primary is already trying
the backup on `RateLimitError`/`APIError`/`APITimeoutError`. During an outage,
the primary wastes latency (timeout duration) on every call before failing
over. Two ways to bypass that:

1. **Feature flag swap** — a flag that makes the factory return the backup as
   primary. Fastest path if you have a flag framework.

   ```python
   def make_llm():
       if feature_flag("llm_failover_to_openai"):
           return ChatOpenAI(model="gpt-4o")
       return ChatAnthropic(model="claude-sonnet-4-6")
   ```

2. **`max_retries=0` on primary** — during outage, set the primary's
   `max_retries=0` via config reload. The primary fails on first attempt,
   `.with_fallbacks` kicks in immediately, and you save the retry-backoff
   latency.

## User-facing comms

### Status page template (public)

```
[Monitoring] Degraded performance — {feature name}
Posted: {timestamp}

We are currently experiencing degraded performance on {feature name} due to
an upstream AI provider incident. Requests may be slower than usual or return
errors. We have failed over to a backup provider and are monitoring the
situation.

Updates will be posted here.
```

Update as it resolves:

```
[Resolved] Degraded performance — {feature name}
Posted: {timestamp}

The upstream provider incident has been resolved and we have returned to
normal operation. Total duration: {N} minutes. No action required.
```

### Internal Slack update (on-call channel)

```
:rotating_light: LLM provider outage — Anthropic
Detected: {timestamp}
Confirmation: status page red + canary failing + app error rate {N}%
Mitigation: failover to OpenAI via feature flag llm_failover_to_openai
Cost impact: OpenAI pricing differs — watch cost-per-req SLO
Next update: in 30 minutes, or on resolution
IC: @{your name}
Trace sample: {langsmith url}
```

## Post-outage checklist

- [ ] Flip the failover flag back when status page returns to green AND canary
      passes for 5+ minutes (do not flip on status-page-only — vendors often
      close incidents optimistically).
- [ ] Close user-facing status page entry.
- [ ] Post internal all-clear in Slack with total duration and cost delta
      (backup provider may have been more/less expensive).
- [ ] File post-mortem ticket. Check: did the breaker open correctly? Did the
      canary fire early enough? Did comms land in under 15min?
- [ ] Update the canary threshold if it did not fire early enough.

## What does NOT belong in the outage playbook

- **Rollbacks.** A provider outage is not your code's fault; a rollback does
  nothing.
- **Scale-up.** More instances do not help when the upstream is the
  bottleneck.
- **Cache purges.** Caches protect you during outages — do not invalidate them.
- **New features.** Do not deploy during an active incident except for the
  failover flip itself.

## Provider-specific notes

- **Anthropic** publishes regional status (us-east, eu-west). Check the
  endpoint the outage affects — your app may be fine if it uses a different
  region.
- **OpenAI** status page aggregates multiple products (API, ChatGPT, image).
  The "API" component is the one that affects LangChain.
- **Azure OpenAI** has per-deployment quotas that look like outages. If your
  deployment is at 0 RPM but the Azure status page is green, your quota was
  exhausted or revoked — not an outage.
