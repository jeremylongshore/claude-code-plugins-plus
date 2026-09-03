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

## Timeout budget

Cap total chain latency. When the chain is client-side, track a budget across attempts:

```python
import time

def complete_with_budget(client, messages, budget_seconds=20, max_tokens=200):
    start = time.time()
    chain = ["orcarouter/fusion", "anthropic/claude-sonnet-4.6", "openai/gpt-4o-mini"]
    for model in chain:
        if time.time() - start > budget_seconds:
            raise TimeoutError(f"budget {budget_seconds}s exhausted")
        try:
            return client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens, timeout=5
            )
        except Exception as e:
            print(f"  hop {model} failed: {e}")
    raise RuntimeError("all hops failed")
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
