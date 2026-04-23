# Trace Metadata and Tagging

`RunnableConfig` is how per-request context travels through a chain. This
reference is the authoritative convention guide — pick these early, because
LangSmith has no rename tool for tags or metadata keys.

## `RunnableConfig` shape

```python
from langchain_core.runnables import RunnableConfig

config: RunnableConfig = {
    "callbacks": [meter],                  # LIST of BaseCallbackHandler instances
    "tags":     ["env:prod", "tenant:acme"],
    "metadata": {"request_id": req_id},
    "run_name": "agent_main",              # LangSmith UI display name
    "recursion_limit": 25,                 # LangGraph — not observability, but lives here
    "configurable": {                      # runtime config consumed by Runnables
        "thread_id": session_id,
        "tenant_id": tenant_id,            # MetricCallback reads this to tag metrics
    },
    "max_concurrency": 10,                 # batch concurrency
}
```

Pass the same `config` dict through every invocation. Reusing a `config` across
concurrent requests is safe as long as `callbacks` is immutable (our
`MetricCallback` is not — it has mutable `_starts` and `_seen` dicts, so
construct one per request).

## Tag conventions

LangSmith treats tags as a flat list. Filtering is exact-match on the full
string. Use hierarchical `key:value` format:

| Tag pattern | Purpose | Example |
|-------------|---------|---------|
| `env:<name>` | Environment | `env:prod`, `env:staging` |
| `tenant:<id>` | Tenant / customer | `tenant:acme-corp` |
| `tier:<plan>` | Plan / tier | `tier:enterprise`, `tier:starter`, `tier:free` |
| `feature:<flag>` | Feature flag / A-B arm | `feature:new-retriever`, `feature:control` |
| `route:<name>` | API route / use case | `route:chat`, `route:summarize` |
| `version:<x>` | App / model version | `version:v2.3.1` |

Bad tags (no one can filter on these): `"important"`, `"check me"`,
`"new feature"`. They end up as unfilterable noise.

Keep tags bounded. More than ~10 tags per run starts to degrade UI rendering.

## Metadata conventions

Metadata is key-value and searchable in the LangSmith UI by key. Use for
higher-cardinality data that you want preserved but not filter-first:

| Key | Purpose |
|-----|---------|
| `request_id` | Correlation with HTTP logs / APM |
| `user_id` | End-user identifier (not for PII — hash if needed) |
| `session_id` | Conversation / `thread_id` |
| `app_version` | Your app version at request time |
| `model_version` | Pinned provider model (`claude-sonnet-4-6`) |
| `experiment_id` | Eval run tag |

Metadata values should be strings or primitives. Nested dicts work but UI
rendering gets cramped — keep shallow.

## `run_name` — single most useful field

The LangSmith UI defaults to showing the Runnable class name (e.g.,
`RunnableSequence`, `AgentExecutor`) which is nearly useless for debugging. Set
`run_name` to a semantic label:

```python
config = {"run_name": "support_ticket_classifier", ...}
```

Common conventions:
- Top-level entrypoint: `run_name="{route}_{operation}"` (`chat_invoke`,
  `document_summarize`)
- Inside a multi-stage chain, set `run_name` on sub-runnables via
  `.with_config(run_name="embedding_step")`

## Per-runnable config (precedence)

Config merges top-down. Invocation-time config wins over definition-time
`.with_config()`, which wins over per-Runnable constants.

```python
step = retriever.with_config(tags=["stage:retrieve"])   # definition-time
result = chain.invoke(inputs, config={"tags": ["env:prod"]})   # invocation-time
# Result tags: ["env:prod", "stage:retrieve"]  (merged)
```

Callbacks are LIST-merged (both fire). Tags are LIST-merged (both appear).
Metadata dict is key-wise merged (invocation-time wins on conflict).

## Wiring `tenant_id` into the callback

The `MetricCallback` takes `tenant_id` in its constructor (Step 2 of the main
skill). For request-handler wiring:

```python
@app.post("/chat")
async def chat_endpoint(req: ChatRequest, user: User = Depends(auth)) -> ChatResponse:
    tenant_id = user.tenant_id
    meter = MetricCallback(tenant_id=tenant_id, sink=app.state.metric_sink)
    config: RunnableConfig = {
        "callbacks": [meter],
        "tags": [f"env:{settings.ENV}", f"tenant:{tenant_id}", f"tier:{user.tier}"],
        "metadata": {
            "request_id": req.request_id,
            "user_id": hash_user_id(user.id),
            "session_id": req.session_id,
        },
        "run_name": "chat_agent",
        "configurable": {"thread_id": req.session_id, "tenant_id": tenant_id},
    }
    result = await chat_agent.ainvoke(req.model_dump(), config=config)
    return ChatResponse(message=result["output"])
```

A fresh `MetricCallback` per request is intentional — it captures per-request
`tenant_id` cleanly and has no cross-request state.

## Propagation into subgraphs (P28)

Config passed at invoke time propagates to subgraphs automatically. Tags and
metadata set via `.with_config()` on the parent runnable do NOT.

```python
# subgraph inherits config["callbacks"] and config["metadata"] — works
await parent.ainvoke(x, config={"callbacks": [meter], "metadata": {"req_id": r}})

# subgraph does NOT inherit .with_config() — broken silently
parent.with_config(callbacks=[meter]).invoke(x)     # P28
```

This is the single most common trace-metadata bug in LangGraph 1.0.

## Reading config inside a Runnable

If your custom Runnable needs to read tenant info, use
`RunnablePassthrough.assign()` or accept `config: RunnableConfig`:

```python
from langchain_core.runnables import RunnableLambda, RunnableConfig

def _handler(inputs: dict, config: RunnableConfig) -> dict:
    tenant = config["configurable"].get("tenant_id", "unknown")
    ...

step = RunnableLambda(_handler)
```

The `config` argument is injected automatically when the lambda signature
includes it.

## References

- [`RunnableConfig` API](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.config.RunnableConfig.html)
- [LangSmith filtering](https://docs.smith.langchain.com/how_to_guides/monitoring/filter_traces_in_application)
- Pack pain catalog: P28 (invocation-time callback propagation)
