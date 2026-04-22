# Token Accounting Pitfalls

Every cost dashboard that disagrees with a provider's billing console has one
of these five causes. The mitigation for each is small; the reconciliation
procedure at the bottom catches what remains.

## 1. Streaming lag via `on_llm_end` (P01)

**Where it bites:** `ChatAnthropic.stream()` only populates
`response_metadata["token_usage"]` at stream close. If your dashboard reads
`on_llm_end`, it lags by the stream duration — 5-30s for long completions,
enough to make real-time cost caps useless.

**Fix:** Use `astream_events(version="v2")` and aggregate from
`on_chat_model_stream` events. Anthropic populates `usage_metadata` on the
`message_start` event (input tokens) and the `message_delta` event
(incremental output). OpenAI populates only on the final chunk. Both surface
as `on_chat_model_stream` in `astream_events`.

```python
async def metered(chain, inputs, meter):
    async for event in chain.astream_events(inputs, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if getattr(chunk, "usage_metadata", None):
                meter.record(event["run_id"], chunk.usage_metadata)
```

## 2. Retry double-counting (P25)

**Where it bites:** Retry middleware invokes the model twice on transient
errors. Both emit `on_llm_end` with their own generation. If the meter keys on
`prompt_hash`, both get summed — the dashboard shows 2x the real spend. If the
meter keys on `run_id`, the second run is a fresh run (new UUID) and still
gets summed.

**Fix:** Attach a stable `request_id` at the chain entry:

```python
from uuid import uuid4
config = {"metadata": {"request_id": str(uuid4())}}
await chain.ainvoke(inputs, config=config)
```

The meter reads `event["metadata"]["request_id"]` and applies "last emission
wins" per `request_id` (see Step 3 in the main skill).

**Alternative:** Put token accounting *above* the retry middleware in the
chain composition, so retries happen inside a scope the meter does not see.
This hides retry activity from observability, which is rarely what you want —
most teams keep retries visible and dedupe.

## 3. Anthropic prompt cache aggregation (P04)

**Where it bites:** `input_token_details.cache_read` is reported per-call.
Summing "total cache savings" naively gives you a per-call value that resets
every request. Teams look at the dashboard, see "cache savings: 4000 tokens",
and miss that caching has saved millions cumulatively.

**Fix:** Aggregate per-session and per-tenant. See the `CacheLedger` sketch in
Step 5 of the main skill and [Cache Economics](cache-economics.md) for the
break-even math.

Key Anthropic usage fields:

| Field | Meaning | Billing factor |
|---|---|---|
| `input_tokens` | Total input (includes both cached and uncached) | Varies by mix |
| `input_token_details.cache_read` | Subset read from cache | 0.10x input rate |
| `input_token_details.cache_creation` | Subset that populated the cache | 1.25x input rate |

Uncached input = `input_tokens - cache_read - cache_creation`. Never assume
`input_tokens` is uncached.

## 4. OpenAI reasoning tokens (o1, o3)

**Where it bites:** `output_token_details.reasoning` is the internal reasoning
trace for o1 and o3 — billed at the output rate but not visible in `content`.
A call with `output_tokens=500` and `reasoning=2000` actually bills 2500
output tokens. Dashboards that sum `output_tokens` only undercount o1/o3 spend
by the reasoning multiple.

**Fix:** Add reasoning to your output-billable total:

```python
def output_billable(m: AIMessage) -> int:
    details = (m.usage_metadata or {}).get("output_token_details", {}) or {}
    return (m.usage_metadata or {}).get("output_tokens", 0) + details.get("reasoning", 0)
```

## 5. Subgraph callbacks not propagating (P28, related)

**Where it bites:** In LangGraph, if a callback handler is attached at the
top-level chain only, subgraph invocations may not emit callbacks. The meter
sees the outer call but not the inner one.

**Fix:** Pass callbacks through `config={"callbacks": [meter], "run_name": ...}`
on every invoke, not constructor-time. LangChain 1.0 propagates config through
subgraphs when passed on invoke.

## Reconciliation procedure

Weekly — or after any instrumentation change — reconcile your meter against
the provider console for a 24h window:

1. **Pull the provider CSV.** Anthropic Console → Usage → Export.
   OpenAI → Usage → Export to CSV.
2. **Sum your meter totals** for the same window.
3. **Compute delta.** `(your_total - provider_total) / provider_total`.
4. **Expected delta:** Within ±1%. Provider rounding accounts for ~0.3%.
5. **If delta > 5%:** Run the four checks above in order. Most often it is
   retries (P25) or streaming (P01). If your meter is *above* provider by more
   than 5%, check for double-attachment of callbacks on nested chains.

Keep the last 8 weekly reconciliations in a JSONL log so you can see drift
trending before it becomes a regression.

## Canonical field access

Use `AIMessage.usage_metadata`, not `response_metadata["token_usage"]`. The
latter has provider-specific shape:

- Anthropic: `response_metadata["usage"]["input_tokens"]`
- OpenAI: `response_metadata["token_usage"]["prompt_tokens"]`
- Gemini: `response_metadata["prompt_feedback"]["token_count"]`

`usage_metadata` is provider-agnostic. Use it everywhere; your cost accounting
survives provider switches.
