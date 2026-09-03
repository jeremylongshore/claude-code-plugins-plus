# OrcaRouter Model Routing — References

## Routing by cost ceiling

The `orcarouter/fusion-*` panels are a coarse cost lever: `fusion` is the frontier panel, `fusion-mini` a leaner two-model panel, `fusion-flash` a budget panel. For a hard ceiling, pin a model with known pricing.

```python
# Cost-aware: prefer the flash panel for high volume
r = client.chat.completions.create(
    model="orcarouter/fusion-flash",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=150,
)
```

## Reading the routing decision

When you call a named `orcarouter/*` router, the concrete model that served the request is reported in the `X-Orca-Resolved-Model` response header, not in the response body's `model` field. Log the header:

```python
from openai import OpenAI
import os, json

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

def log_resolved_model(resp, request_id):
    # The raw response exposes headers; the resolved model is X-Orca-Resolved-Model.
    entry = {
        "request_id": request_id,
        "requested_model": resp.model,
        "finish_reason": resp.choices[0].finish_reason,
        "tokens": resp.usage.total_tokens,
    }
    print(json.dumps(entry))
```

With cURL, dump headers and grep:

```bash
curl -si https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"orcarouter/auto","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}' \
  | grep -iE '^x-orca-(router|resolved-model)'
```

## Comparison harness

```python
models = ["orcarouter/fusion", "orcarouter/fusion-flash", "orcarouter/fusion-mini", "orcarouter/auto"]
prompt = "Summarize the Python GIL in two sentences."

for m in models:
    r = client.chat.completions.create(model=m, messages=[{"role": "user", "content": prompt}], max_tokens=120)
    print(m, "->", r.choices[0].message.content[:40], "| tokens:", r.usage.total_tokens)
```

## Fallback chains

OrcaRouter supports server-side fallback chains via `extra_body.models`. If the first model fails, the gateway tries the next:

```python
r = client.chat.completions.create(
    model="orcarouter/fusion",  # primary
    messages=[{"role": "user", "content": "Critical task"}],
    max_tokens=200,
    extra_body={
        "models": ["orcarouter/fusion", "anthropic/claude-sonnet-4.6", "openai/gpt-4o-mini"],
    },
)
```

The `X-Orca-Fallback-Level` and `X-Orca-Fallback-Model` response headers tell you whether a fallback triggered. See [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks).

## Next skills

- `orcarouter-fallback-reliability` — failover chains and retry policies
- `orcarouter-cost-observability` — budgets and per-request cost tracking
