# OrcaRouter Fallback & Reliability — References

## Server-side fallback chain

Prefer the gateway's native fallback chain over hand-rolled client chains. Put an ordered list in `extra_body.models` with `route: "fallback"` (max 5, same endpoint type recommended). Free models are dropped from a chain below the first position — a `-free` id can be the primary but a chain never fails over into free capacity. Billing is for the model that actually served. See [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks).

```python
r = client.chat.completions.create(
    model="anthropic/claude-sonnet-4.6",
    messages=[{"role": "user", "content": "Critical task"}],
    max_tokens=200,
    extra_body={
        "models": ["anthropic/claude-sonnet-4.6", "openai/gpt-4o-mini", "google/gemini-2.5-flash"],
        "route": "fallback",
    },
)
```

## Circuit breaker

Avoid hammering a failing model. Track consecutive failures per model and skip it for a cooldown window:

```python
import time
from collections import defaultdict

class CircuitBreaker:
    def __init__(self, failure_threshold=3, cooldown_seconds=30):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = defaultdict(int)
        self.open_until = defaultdict(float)

    def is_open(self, model):
        return time.time() < self.open_until[model]

    def record_success(self, model):
        self.failures[model] = 0

    def record_failure(self, model):
        self.failures[model] += 1
        if self.failures[model] >= self.failure_threshold:
            self.open_until[model] = time.time() + self.cooldown_seconds
            self.failures[model] = 0
            print(f"circuit opened for {model} for {self.cooldown_seconds}s")
```

## Retry classification

The only retryable failures are transport errors, `408`, `429`, and `5xx`. Everything else — `400`, `401`, `402`, `403`, `404`, `422`, and the policy blocks (`guardrail_blocked`, `firewall_blocked`, `firewall_approval_pending`) — is deterministic and must propagate on the first attempt. Keep the classifier as an allow-list so an unrecognized exception type fails closed:

```python
from openai import APIConnectionError, APITimeoutError, APIStatusError

RETRYABLE_STATUS = {408, 429}
POLICY_CODES = {"guardrail_blocked", "firewall_blocked", "firewall_approval_pending"}

def error_code(e):
    body = getattr(e, "body", None)
    err = body.get("error") if isinstance(body, dict) else None
    return err.get("code") if isinstance(err, dict) else None

def is_retryable(e):
    if isinstance(e, (APIConnectionError, APITimeoutError)):
        return True
    if isinstance(e, APIStatusError):
        if error_code(e) in POLICY_CODES:
            return False
        return e.status_code in RETRYABLE_STATUS or 500 <= e.status_code < 600
    return False

def retry_after_seconds(e):
    resp = getattr(e, "response", None)
    raw = resp.headers.get("retry-after") if resp is not None else None
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return None  # absent or HTTP-date form -> exponential backoff
```

`Retry-After` is honored when present and numeric; otherwise back off exponentially with jitter. Never sleep-and-resend a policy verdict.

## Timeout budget

Cap total chain latency. When the chain is client-side, track a budget across attempts and hop only on retryable failures:

```python
import time
from openai import APIConnectionError, APITimeoutError, APIStatusError

def complete_with_budget(client, messages, budget_seconds=20, max_tokens=200):
    start = time.time()
    chain = ["orcarouter/fusion", "anthropic/claude-sonnet-4.6", "openai/gpt-4o-mini"]
    last_error = None
    for model in chain:
        if time.time() - start > budget_seconds:
            raise TimeoutError(f"budget {budget_seconds}s exhausted") from last_error
        try:
            return client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens, timeout=5
            )
        except (APIConnectionError, APITimeoutError, APIStatusError) as e:
            # A hop only absorbs retryable failures. A guardrail/policy denial or a
            # malformed request is deterministic and must not be masked by hopping.
            if isinstance(e, APIStatusError) and not (
                e.status_code in (408, 429) or 500 <= e.status_code < 600
            ):
                raise
            last_error = e
            print(f"  hop {model} failed: {e}")
    raise RuntimeError("all hops failed") from last_error
```

## Idempotency for agent tool calls

For agent-tool-governed environments, tag requests so retries are safe:

```python
r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=messages,
    max_tokens=200,
    extra_body={"metadata": {"request_id": "req_123", "agent": "my-agent"}},
)
```

## Verifying the chain in prod

Read the `X-Orca-Fallback-Level` and `X-Orca-Fallback-Model` response headers to see which model served:

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

response = client.chat.completions.with_raw_response.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)
headers = response.headers
served = headers.get("X-Orca-Fallback-Model", headers.get("X-Orca-Resolved-Model", "unknown"))
print("served by:", served)
```

## Next skills

- `orcarouter-cost-observability` — budgets and cost tracking across the chain
- `orcarouter-agent-security` — gateway-level guardrails and tool governance
