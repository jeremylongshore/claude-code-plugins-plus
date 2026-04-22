# Token Accounting Across Providers

Token counts are not reported the same way by the three major providers, and
LangChain 1.0 passes provider quirks through verbatim. This reference documents
where the counts actually appear and how to aggregate them correctly.

## The key field: `usage_metadata`

LangChain 1.0 standardizes on `AIMessage.usage_metadata` (and `AIMessageChunk`
for streaming). Shape:

```python
{
    "input_tokens": int,
    "output_tokens": int,
    "total_tokens": int,
    "input_token_details": {"cache_read": int, "cache_creation": int, ...},  # Anthropic
    "output_token_details": {"reasoning": int, ...},                          # OpenAI o1
}
```

Use `usage_metadata` for aggregation, not `response_metadata["token_usage"]`
(which has per-provider shape).

## Streaming (P01)

On a standard `.invoke()` call, `usage_metadata` is populated on the returned
`AIMessage`. On `.stream()` and `.astream()`, it is populated on the **final
chunk only** — intermediate chunks have `usage_metadata = None` or partial data.

**Wrong:** subscribing to `on_llm_end` to read total tokens — this fires once,
after the stream closes, so dashboards lag by stream duration.

**Right:** `astream_events(version="v2")` + `on_chat_model_stream`:

```python
meter = {"in": 0, "out": 0}
async for event in chain.astream_events({"messages": [...]}, version="v2"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        if chunk.usage_metadata:
            # OpenAI: populated only on final chunk
            # Anthropic: populated on `message_start` and `message_delta` events
            meter["in"] += chunk.usage_metadata.get("input_tokens", 0)
            meter["out"] += chunk.usage_metadata.get("output_tokens", 0)
```

For real-time token-level cost in the UI, count output tokens via
`tiktoken` / `anthropic.Anthropic().count_tokens()` on the text delta you just
rendered. Do not wait for `usage_metadata`.

## Prompt caching (Anthropic) — P04

Anthropic reports cache hits in `input_token_details`:

```python
msg.usage_metadata["input_token_details"]
# {"cache_creation": 0, "cache_read": 4123}
```

Aggregating "total cache savings" requires summing `cache_read` across *all*
calls in a session or tenant. LangChain does not do this for you.

## OpenAI reasoning tokens (o1, o3)

`output_token_details.reasoning` is the internal reasoning tokens — billed but
not visible in `content`. A call with `output_tokens=500` and
`output_token_details.reasoning=2000` actually costs 2500 output tokens.

Include reasoning tokens in cost math:

```python
def output_billable(m: AIMessage) -> int:
    details = m.usage_metadata.get("output_token_details", {})
    return m.usage_metadata["output_tokens"] + details.get("reasoning", 0)
```

## Gemini specifics

Gemini reports counts on every streaming chunk (not just the last). Sum them
directly. Gemini does not have a cache equivalent.

## Rate-limit vs billing dimensions

Anthropic bills on tokens but *rate-limits* on RPM and ITPM (input tokens per
minute) separately. A high-cache workload can hit RPM limits long before ITPM.
See `langchain-rate-limits` skill.

## Callback-based aggregation (multi-turn)

For chat sessions, attach a callback that aggregates across turns:

```python
from langchain_core.callbacks import BaseCallbackHandler

class TokenMeter(BaseCallbackHandler):
    def __init__(self):
        self.input_total = 0
        self.output_total = 0
        self.cache_read_total = 0

    def on_llm_end(self, response, **kwargs) -> None:
        for gen in response.generations:
            for g in gen:
                meta = g.message.usage_metadata or {}
                self.input_total += meta.get("input_tokens", 0)
                self.output_total += meta.get("output_tokens", 0)
                self.cache_read_total += (
                    meta.get("input_token_details", {}).get("cache_read", 0)
                )
```

Pass via `config={"callbacks": [meter]}` on invoke so callbacks propagate to
subgraphs (P28).

## Verify against provider dashboards

Token counts reported by `usage_metadata` should match the provider's billing
dashboard within ~1% for a 24-hour window. If your counts are off by >5%,
suspect: (a) retries double-counted (P25), (b) subgraph callbacks not propagating
(P28), (c) streaming `on_llm_end` missed.
