# Latency Triage — p95 vs p99, Cold Start Detection, Provider vs App Attribution

When a latency alert fires, the first decision is **which percentile** moved.
p95 and p99 degradations have different root causes and different fixes.
Fixing the wrong one wastes the incident window.

## Shape-reading: what the percentile tells you

| Shape | Likely cause | First check |
|---|---|---|
| p95 up, p99 up proportionally, TTFT up | Provider-side latency, or network | Provider status page; provider-side request-start logs if available |
| p95 stable, p99 spiky, spikes align with instance starts | **Cold start** (P36) | `kubectl get pods` / `gcloud run services describe` — count pod starts in window |
| p95 up, p99 up, TTFT unchanged | Output-length regression — model is generating more tokens | LangSmith: compare avg output tokens in window vs baseline |
| TTFT up, total latency unchanged | Provider-side queuing or prompt-caching miss | Anthropic: check cache hit rate; OpenAI: check `usage.prompt_tokens_details.cached_tokens` |
| p95 stable, p99 up, spikes on long-running sessions | Agent recursion depth increased (P10 adjacent) | LangSmith: step-count histogram per trace |
| All percentiles up on a single pod/instance | Bad deploy or resource exhaustion on that instance | Per-instance latency breakdown; recycle the instance |

## Cold-start detection (P36)

Cloud Run, Lambda, Vercel — any platform that scales to zero — produces a
p99 that is 10x p95 because the first request after a cold start pays the full
Python import + LangChain initialization tax (5–15s for a typical stack with
embeddings + FAISS preloaded at module level).

**Detection query (LangSmith or equivalent):**

```
# Pseudo-query: correlate p99 spikes with instance age < 30s
- filter: latency > 10s AND service = "my-service"
- join: container_start_timestamp (from platform metrics)
- group by: latency_bucket, instance_age_bucket
```

If the histogram shows 90% of >10s traces happening on instances <30s old, it
is a cold start. The fix is **not** more CPU — it is `--min-instances=1`
(Cloud Run), `provisioned_concurrency` (Lambda), or a keepalive pinger (every
5min, to keep at least one warm instance).

**Quick Cloud Run fix:**

```bash
gcloud run services update my-langchain-service \
  --min-instances=1 \
  --cpu-always-allocated
```

CPU-always-allocated changes billing (you pay when the instance is idle) but
halves cold-start time on many stacks because module-level imports stay warm
in memory during idle periods.

**Module-level preload:** any heavy import (SentenceTransformers, FAISS index
load, ChatAnthropic construction) at module top level is paid at cold start,
not first request. Move them inside a `startup` hook if your framework has
one, or keep them at module level and accept the cold-start cost — but do not
put them inside the request handler, which makes **every** request pay the
cost.

## Streaming diagnosis

TTFT only has a value if you are streaming. If your app is using
`.invoke()` instead of `.stream()` / `.astream()`, TTFT and total latency
are the same number and the TTFT SLO is meaningless.

**Check:** in LangSmith, inspect a slow trace — if the model span has a single
output event at the end, you are not streaming. If it has incremental output
events, you are.

**Fix for FastAPI + LangChain:**

```python
from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat(body: ChatRequest):
    return StreamingResponse(
        (chunk.content async for chunk in chain.astream(body.input)),
        media_type="text/plain",
    )
```

Streaming also helps bypass Vercel's 10s function timeout (P35 adjacent) — the
first byte going out the door resets the connection-idle clock on most
platforms.

## Provider-side vs app-side attribution

The fastest way to split provider latency from your own:

1. In LangSmith, open the slow trace.
2. Check the model span duration — that is **provider wall-clock time** (request
   sent → final token received at your process).
3. Subtract from the total trace duration — that is **your app overhead**
   (routing, retriever, tool calls between model steps, serialization).

If the model span alone is 8s, the provider is slow — no amount of app-side
tuning will fix it. Check provider status, consider failing over.

If the model span is 800ms but the trace is 8s, you have app overhead — a slow
retriever, an N+1 tool call, a synchronous DB query in a `RunnableLambda`. Run
`langchain-debug-bundle` if available.

## When to page vs when to wait

- **Page immediately:** p95 TTFT burn-rate > 2% in 5min (fast burn) AND
  provider status page is green → your bug.
- **Page immediately:** p99 > 10s AND sustained 15min → user-visible
  degradation even if intermittent.
- **Wait, file a ticket:** p99 spiky but p95 healthy, matches cold-start
  pattern → fix with `--min-instances=1` at next deploy window unless traffic
  is ramping.
- **Wait, file a ticket:** slow-burn alerts (1h window) → likely a gradual
  regression, not an outage; triage in business hours.

## Recovery verification

After applying a fix (min-instances=1, streaming enabled, etc.), wait at
least **one full p99 window** before declaring all-clear. If your window is
5min, that means 5 minutes of clean metrics. Do not close the incident on
"looks better" — close on "SLO back under threshold for N minutes."
