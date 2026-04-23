# Retry Middleware and Telemetry Deduplication

Retry middleware re-runs a failed model call. Both attempts emit
`on_llm_end`. The token-usage aggregator sees both, sums them, and bills
twice for one logical call. That is P25. The fix is to attach a stable
`request_id` to every retry attempt so the aggregator deduplicates by id,
not by position in the event stream.

## The P25 failure in detail

```
t=0.0s  model.invoke(...)   → anthropic.RateLimitError
t=0.1s  callback emits on_llm_end { tokens: 0 }   # phantom: retry counts this
t=1.0s  retry attempt 2
t=1.5s  model.invoke(...)   → success
t=1.5s  callback emits on_llm_end { tokens: 1523 }
```

A naive aggregator sums `0 + 1523 = 1523` — correct. But on a retry that
*partially* billed (some providers charge for the failed attempt if bytes were
sent to the model), the first `on_llm_end` is non-zero:

```
t=0.0s  model.invoke(...) → anthropic.APIError (after 800ms; provider billed the 500 input tokens)
t=0.8s  callback emits on_llm_end { tokens: 500 }
t=1.8s  retry succeeds
t=3.0s  callback emits on_llm_end { tokens: 2023 }
Aggregator: 500 + 2023 = 2523. Actual billable: 500 + 2023 = 2523 ✓  (this case is correct)
```

**Where it breaks:** provider-side timeouts that bill the full input plus a
partial output, and then the retry sends the same input again and bills for
*another* full input+output. The aggregator sees two events, both non-zero,
and sums them — but the user's session ledger now double-counts the
deliberately-identical input tokens because retry resent them for reliability,
not because the user asked for two completions.

The solution: tag the attempt with a shared `request_id`, and make the
aggregator's rule explicit — *record usage only from the last successful
attempt for a given request_id*.

## Reference implementation

```python
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Callable

RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    TimeoutError,
    ConnectionError,
    # Import provider-specific ones in your app:
    # anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIStatusError,
    # openai.RateLimitError, openai.APITimeoutError,
    # google.api_core.exceptions.ResourceExhausted,
)

@dataclass
class RetryPolicy:
    max_retries: int = 2
    base_delay: float = 1.0
    jitter: float = 0.2          # +/- 20% randomness
    max_delay: float = 30.0

def delay(policy: RetryPolicy, attempt: int) -> float:
    import random
    exp = policy.base_delay * (2 ** attempt)
    jittered = exp * (1 + random.uniform(-policy.jitter, policy.jitter))
    return min(jittered, policy.max_delay)

def with_retry(model_invoke: Callable, policy: RetryPolicy = RetryPolicy()):
    def _call(inputs: dict) -> dict:
        request_id = inputs.get("request_id") or str(uuid.uuid4())
        inputs = {**inputs, "request_id": request_id}
        last_err = None
        for attempt in range(policy.max_retries + 1):
            try:
                return model_invoke({**inputs, "attempt": attempt})
            except RETRYABLE_EXCEPTIONS as e:
                last_err = e
                if attempt == policy.max_retries:
                    break
                time.sleep(delay(policy, attempt))
        raise last_err
    return _call
```

## Dedup-by-request_id aggregator

The aggregator is a callback handler that records token usage keyed by
`request_id`. On every `on_llm_end`, it **replaces** any previous record for
that `request_id` — the last successful attempt wins, the earlier failed
attempts are discarded.

```python
from langchain_core.callbacks import BaseCallbackHandler

@dataclass
class TokenAggregator(BaseCallbackHandler):
    # Keyed by request_id so P25 double-count is impossible:
    _per_request: dict[str, dict[str, int]] = field(default_factory=dict)
    _per_session: dict[str, dict[str, int]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def on_llm_end(self, response, **kwargs) -> None:
        request_id = kwargs.get("metadata", {}).get("request_id")
        session_id = kwargs.get("metadata", {}).get("session_id", "anonymous")
        if not request_id:
            # No request_id attached — cannot dedupe. Log and fall through.
            # In strict mode, raise so the caller fixes the middleware order.
            return
        usage = getattr(response, "llm_output", {}) or {}
        tokens_in  = usage.get("token_usage", {}).get("prompt_tokens", 0)
        tokens_out = usage.get("token_usage", {}).get("completion_tokens", 0)
        with self._lock:
            # REPLACE, not add. Last successful attempt wins.
            self._per_request[request_id] = {"in": tokens_in, "out": tokens_out}
            # Session totals: rebuild from per_request to stay consistent.
            sess = self._per_session.setdefault(session_id, {"in": 0, "out": 0})
            sess["in"]  = sum(r["in"]  for r in self._per_request.values())
            sess["out"] = sum(r["out"] for r in self._per_request.values())

    def session_usage(self, session_id: str) -> dict[str, int]:
        with self._lock:
            return dict(self._per_session.get(session_id, {"in": 0, "out": 0}))
```

**Key rule:** `_per_request[request_id]` is **replaced** on every successful
`on_llm_end`. Failed attempts either never fire `on_llm_end` (depending on the
provider integration) or fire with `error` set — which the aggregator can
filter. Either way, the final value for a `request_id` reflects only the
successful attempt.

## Retryable exception list (provider-specific)

Do not catch `Exception`. It catches `KeyboardInterrupt` on Python < 3.12
(P07) and swallows programmer errors.

### Anthropic

```python
from anthropic import (
    RateLimitError,        # 429
    APITimeoutError,       # network timeout
    APIConnectionError,    # connection failed
    InternalServerError,   # 500, 502, 503, 504
    APIStatusError,        # subclass filter to 5xx only
)
RETRYABLE_ANTHROPIC = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)
```

**Do NOT retry:** `BadRequestError` (400), `AuthenticationError` (401),
`PermissionDeniedError` (403), `NotFoundError` (404). These will never succeed
on retry.

### OpenAI

```python
from openai import RateLimitError, APITimeoutError, APIConnectionError, InternalServerError
RETRYABLE_OPENAI = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)
```

### Google Gemini

```python
from google.api_core.exceptions import (
    ResourceExhausted,     # 429
    DeadlineExceeded,      # timeout
    ServiceUnavailable,    # 503
    InternalServerError,   # 500
)
RETRYABLE_GEMINI = (ResourceExhausted, DeadlineExceeded, ServiceUnavailable, InternalServerError)
```

## Exponential backoff with jitter

Without jitter, all retrying clients synchronize — they all back off by the
same amount, slam the provider at `t=delay`, and trigger another 429. Jitter
staggers the retry wave.

```python
import random
def delay(policy: RetryPolicy, attempt: int) -> float:
    exp = policy.base_delay * (2 ** attempt)
    jittered = exp * (1 + random.uniform(-policy.jitter, policy.jitter))
    return min(jittered, policy.max_delay)
```

Typical config: `base_delay=1.0`, `max_retries=2`, `jitter=0.2`. That gives
waits of ~1s, ~2s, max ~2.4s. Anything longer for interactive traffic is a
user experience problem — fail fast and let the caller re-try.

## Circuit breaker — stop retrying a dead upstream

After N consecutive failures for a provider, **open the circuit** — stop
issuing new calls for a cooldown period. Otherwise a dead upstream causes a
retry storm that inflates the load and the bill.

```python
@dataclass
class CircuitBreaker:
    fail_threshold: int = 5
    cooldown_s: float = 30.0
    _failures: int = 0
    _opened_at: float | None = None
    _lock: Lock = field(default_factory=Lock)

    def is_open(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return False
            if time.monotonic() - self._opened_at > self.cooldown_s:
                # Half-open: allow one probe
                self._opened_at = None
                self._failures = 0
                return False
            return True

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.fail_threshold:
                self._opened_at = time.monotonic()

class CircuitOpen(Exception):
    pass
```

Wrap the retry middleware: check `breaker.is_open()` before each attempt, raise
`CircuitOpen` immediately on open circuit.

## max_retries=6 is usually wrong (P30)

`ChatOpenAI` defaults to `max_retries=6` — which means 7 actual requests per
logical call. Combined with a 429 storm, a single minute of bad luck costs 7x
as much as expected. Set `max_retries=2` at the model level and compose with
your middleware retry — the middleware layer is the authoritative retry
policy and is aware of the circuit breaker and request_id tagging.

```python
model = ChatAnthropic(model="claude-sonnet-4-6", max_retries=2, timeout=30)
```

## Testing the aggregator dedup

```python
from types import SimpleNamespace

def _mk_response(tokens_in, tokens_out):
    return SimpleNamespace(llm_output={
        "token_usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
    })

def test_aggregator_dedupes_by_request_id():
    agg = TokenAggregator()
    req = "req-xyz"

    # First attempt billed 500 input, 0 output (provider timeout after input sent)
    agg.on_llm_end(_mk_response(500, 0),   metadata={"request_id": req, "session_id": "S1"})
    # Second attempt succeeded: 500 input, 1200 output
    agg.on_llm_end(_mk_response(500, 1200), metadata={"request_id": req, "session_id": "S1"})

    usage = agg.session_usage("S1")
    assert usage == {"in": 500, "out": 1200}, (
        "Aggregator must REPLACE per request_id, not SUM. "
        f"Got {usage}; expected last-attempt values only."
    )

def test_aggregator_without_request_id_is_dropped():
    agg = TokenAggregator()
    agg.on_llm_end(_mk_response(100, 200), metadata={"session_id": "S1"})
    assert agg.session_usage("S1") == {"in": 0, "out": 0}
```

## References

- [LangChain — Callbacks](https://python.langchain.com/docs/concepts/callbacks/)
- [Anthropic SDK — Retries](https://github.com/anthropics/anthropic-sdk-python#retries)
- [OpenAI SDK — Retries](https://github.com/openai/openai-python#retries)
- [AWS: exponential backoff and jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- Pack pain catalog entries **P25, P30**, plus P07 (KeyboardInterrupt), P29 (multi-process rate limiting), P31 (Anthropic tier throttling)
