# Backoff and Retry

How retries, fallbacks, and rate limiters interact when a 429 slips past your limiter anyway — and why the defaults are wrong.

## The three layers

```
request → [max_retries] → [rate_limiter] → [with_fallbacks] → provider
```

Each layer is a separate failure boundary. Understand what each does before tuning.

| Layer | Trigger | Default action | Cost risk |
|---|---|---|---|
| `max_retries` | SDK-level retryable errors (429, 5xx, timeout) | Exponential backoff with jitter, respects `retry-after` | 7x call bill on default `ChatOpenAI` (P30) |
| `rate_limiter` | Pre-call gate (before the request fires) | Block until token available | 0 (prevents requests) |
| `with_fallbacks` | Uncaught exception from primary chain | Try backup chain in order | 2x call bill per level on matched exceptions |

## `max_retries` math

**`max_retries` is retries, not attempts.** `max_retries=6` means: initial attempt + up to 6 retries = **7 total requests** for one logical call (P30).

```python
# Default ChatOpenAI
llm = ChatOpenAI(model="gpt-4o")  # max_retries=6 by default

# Worst case on a flaky network: 7 billed requests per .invoke()
# At $0.005/1K input tokens and 2K input/call: $0.07 per logical call
# At 1000 calls/day: $70/day in retry waste instead of $10
```

Recommendation: **`max_retries=2`** and lean on the rate limiter + fallbacks for resilience.

```python
llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    max_retries=2,
    timeout=30,
    rate_limiter=redis_limiter,
)
```

### Retry shape (LangChain / Anthropic SDK default)

Backoff follows `base * (2 ** attempt) + jitter` with a ceiling, AND respects `retry-after` header when the provider sends one. Typical sequence for `max_retries=2`:

1. Attempt 1: fires immediately
2. If 429 with `retry-after: 8`: wait 8s
3. Attempt 2: retry
4. If 429 again: wait `2 * 2 + jitter` = ~4-5s (SDK ignores retry-after past first retry in some versions — verify on your SDK version)
5. Attempt 3 (final retry): if fails, exception propagates

Total wall-clock: 15-30s worst case for `max_retries=2`. At `max_retries=6`: 60-120s.

## Narrowing `exceptions_to_handle` (P07)

`.with_fallbacks([backup])` defaults to `exceptions_to_handle=(Exception,)`. On Python <3.12, `Exception` includes `KeyboardInterrupt` via the inheritance hierarchy in some edge cases (and definitely includes `asyncio.CancelledError`). **Narrow the tuple to specific retryable errors per provider.**

```python
from anthropic import (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)

# Primary: Anthropic. Backup: OpenAI.
resilient = (prompt | claude | parser).with_fallbacks(
    [prompt | gpt4o | parser],
    exceptions_to_handle=(
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
        InternalServerError,
    ),
    # DO NOT include: Exception, BaseException, KeyboardInterrupt,
    # AuthenticationError, BadRequestError, ValidationError
)
```

See the sibling skill `langchain-sdk-patterns` reference `fallback-exception-list.md` for the full per-provider whitelist. **Do not duplicate that content here** — cross-reference.

### Why you never want `Exception`

A `ValidationError` on your Pydantic schema silently falls through to the backup chain, which has the same schema, which produces the same error. Your user gets a delayed failure instead of an immediate one, and you paid twice. `AuthenticationError` is the same — bad API key is a config bug, not a transient issue.

## `Retry-After` header respect

All three providers send `Retry-After` on 429. LangChain's SDKs honor it:

- Anthropic: `retry-after` in seconds (integer) or HTTP-date
- OpenAI: `retry-after-ms` (milliseconds) or `retry-after` (seconds)
- Google: `retry-after` (seconds) or `retry-info` metadata

For observability, log the header on every 429:

```python
from langchain_core.callbacks import BaseCallbackHandler

class RetryAfterLogger(BaseCallbackHandler):
    def on_llm_error(self, error, **kwargs):
        # SDKs attach response headers to the exception
        headers = getattr(error, "response", None)
        if headers is not None:
            retry_after = headers.headers.get("retry-after")
            if retry_after:
                log.warn("rate_limited", retry_after=retry_after, model=kwargs.get("name"))
```

If you see `retry-after` values climbing (2 → 4 → 8 → 16), you are pushing the tier. Back off the rate limiter, do not just keep retrying.

## Retry + rate-limit interaction (the subtle one)

Setup:
- `rate_limiter = InMemoryRateLimiter(requests_per_second=10)`
- `max_retries = 6`

Worst case: every retry goes through the rate limiter. A transient 5xx at the provider causes the client to retry, which blocks on `limiter.acquire()`, which uses a second RPM slot, which extends the total billed count.

**Rule**: rate limiter should be sized for **attempts**, not **logical calls**. If you expect 5% retry rate:

```
target_rpm_on_provider = 50        (Anthropic tier 1)
expected_retry_rate = 0.05
effective_rpm = target_rpm_on_provider / (1 + retry_rate) = 50 / 1.05 ≈ 47
requests_per_second = 47 / 60 ≈ 0.78
```

Monitor real retry rate via callback and adjust periodically.

## Circuit breaker on top

For workloads where repeated 429s indicate a sustained overload (not transient spikes), add a circuit breaker:

```python
from functools import wraps
import time

class CircuitBreaker:
    def __init__(self, fail_threshold=5, reset_after_s=30):
        self.failures = 0
        self.opened_at = None
        self.fail_threshold = fail_threshold
        self.reset_after_s = reset_after_s

    def is_open(self):
        if self.opened_at is None:
            return False
        if time.time() - self.opened_at > self.reset_after_s:
            self.opened_at = None
            self.failures = 0
            return False
        return True

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.fail_threshold:
            self.opened_at = time.time()

    def record_success(self):
        self.failures = 0
```

Wrap invocations: if the breaker is open, short-circuit to a fallback (cache, degraded response, "try again later"). The breaker protects the provider from cascading overload and you from burning billing on sure-fail requests.

## Putting it together

Production-shaped defaults for LangChain 1.0 with a Redis-backed limiter:

```python
from langchain_anthropic import ChatAnthropic
from anthropic import RateLimitError, APITimeoutError, APIConnectionError, InternalServerError

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    max_retries=2,              # NOT 6 — see P30
    timeout=30,
    rate_limiter=redis_limiter, # cluster-wide (see redis-limiter-pattern.md)
)

chain = (prompt | llm | parser).with_fallbacks(
    [prompt | gpt4o | parser],
    exceptions_to_handle=(      # NARROW — see P07
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
        InternalServerError,
    ),
)
```

Three knobs, three jobs:
- `max_retries=2` — absorb transient blips, do not amplify cost
- `rate_limiter` — cluster-wide gate to stop 429s at the source
- `with_fallbacks(narrow_tuple)` — cross-provider continuity when primary is unhealthy

## Cross-references

- [Redis Limiter Pattern](redis-limiter-pattern.md) — where `redis_limiter` comes from
- [Provider Tier Matrix](provider-tier-matrix.md) — sizing targets
- [Measuring Demand](measuring-demand.md) — how to verify the above numbers against your traffic
- `langchain-sdk-patterns/references/fallback-exception-list.md` — full per-provider exception whitelist
