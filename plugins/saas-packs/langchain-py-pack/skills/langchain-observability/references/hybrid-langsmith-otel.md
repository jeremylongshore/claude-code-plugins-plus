# Hybrid: LangSmith + OTEL

Running both LangSmith and OTEL tracing in the same service is a valid
choice — different stacks serve different consumers. But naive "turn both on"
double-emits spans, inflates metric cardinality, and creates conflicting
trace IDs in distributed tracing UIs. This reference is the split-point
contract.

Cross-reference: the deep OTEL integration lives in
`langchain-otel-observability` (L33). This file only covers the split-point
decision, not the OTEL setup itself.

## When to split

Run LangSmith alone when:
- You are a pure LangChain shop (no FastAPI traces in OTEL, no distributed
  services with Jaeger/Tempo)
- Your team uses prompt/response inspection as the primary debugging surface
- You do not already have an OpenTelemetry Collector in the stack

Run OTEL alone when:
- You have a mature OpenTelemetry stack with Collector, Tempo / Jaeger,
  Prometheus — and LLM calls are one service among many
- Data residency / self-hosting requirements block LangSmith
- You want a single pane of glass for HTTP + DB + LLM spans

Run hybrid (both) when:
- You need LangSmith for LLM-specific features (prompt diff, eval datasets,
  annotation queues) AND OTEL for distributed tracing
- You are migrating from LangSmith → OTEL or vice-versa and need overlap
- A specific team (e.g., ML eng) wants LangSmith while platform eng owns OTEL

## Split-point rules

In a hybrid deployment, decide ownership by domain. Do NOT double-emit the
same metric to both stacks.

| Concern | Owner | Why |
|---------|-------|-----|
| Prompt / response content | LangSmith | LLM-native UI, redaction controls |
| LLM token counts (per-run) | LangSmith | Native to LLM runs |
| LLM token counts (aggregated SLO) | Prometheus / OTEL | Alert rules, long-term retention |
| Distributed trace ID | OTEL | End-to-end request correlation across services |
| Per-tenant cost dashboards | Prometheus / OTEL | Grafana, Datadog existing tooling |
| Eval datasets / regressions | LangSmith | Purpose-built for this |
| Model upgrade A/B | LangSmith | Dataset replay is free |
| Infra latency (HTTP, DB) | OTEL | Auto-instrumented by `opentelemetry-instrumentation-*` |

## Trace ID propagation

When both systems are on, you want LangSmith runs and OTEL spans linkable.
Two patterns:

### Pattern A — OTEL is source of truth for trace IDs

Push the OTEL trace ID into LangSmith metadata. LangSmith UI can link out by
search.

```python
from opentelemetry import trace as otel_trace

def get_trace_context() -> dict[str, str]:
    span = otel_trace.get_current_span()
    if not span or not span.get_span_context().is_valid:
        return {}
    ctx = span.get_span_context()
    return {
        "otel_trace_id": f"{ctx.trace_id:032x}",
        "otel_span_id":  f"{ctx.span_id:016x}",
    }

config["metadata"] = {**config.get("metadata", {}), **get_trace_context()}
```

Jumping from OTEL → LangSmith: search by `metadata.otel_trace_id`.

### Pattern B — LangSmith is source of truth; OTEL links back

Less common. The LangSmith run ID is available as `run.id` on the returned
trace object, but reading it back mid-run requires a callback. Skip this
unless you have a specific reason.

## Metric double-emission — how to avoid

If you have a `MetricCallback` pushing to Prometheus AND OTEL auto-instrumentation
collecting HTTP/LLM spans, you can end up counting the same call twice:

| Metric | `MetricCallback` emits? | OTEL instrumentation emits? | Resolution |
|--------|-------------------------|-----------------------------|------------|
| `llm.token_in` | Yes (with tenant_id) | Sometimes (via `opentelemetry-instrumentation-langchain`) | Pick one — the callback version has richer tags, prefer it |
| `llm.latency_ms` | Yes | Yes (as span duration) | OTEL span duration IS the latency — drop from callback |
| `http.server.duration` | No | Yes | OTEL owns — ignore |

The safe default in hybrid mode: the `MetricCallback` owns LLM-specific
metrics with tenant tags; OTEL spans own durations and infra metrics. Do not
count latency in both.

## OTEL span attributes to set

When running hybrid, set these on the active OTEL span from inside the
callback (or from a post-run hook):

```python
from opentelemetry import trace as otel_trace

def on_llm_end(self, response, *, run_id, **kwargs) -> None:
    span = otel_trace.get_current_span()
    if span and span.get_span_context().is_valid:
        meta = ...  # extract from response
        span.set_attribute("llm.tenant_id", self.tenant_id)
        span.set_attribute("llm.token_in",  meta.get("input_tokens", 0))
        span.set_attribute("llm.token_out", meta.get("output_tokens", 0))
        span.set_attribute("llm.model",     meta.get("model", "unknown"))
        # Link LangSmith run for jumpback
        span.set_attribute("langsmith.run_id", str(run_id))
```

Use the OTEL semantic conventions for GenAI
(`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`,
`gen_ai.response.model`) when your stack is modern enough to consume them.

## Privacy: prompt content

LangSmith logs prompt content by default. OTEL's GenAI instrumentation does
NOT log prompt content by default — that is a safety feature (P27).

If you enable both:
- Apply redaction middleware BEFORE model call so both systems see cleaned
  prompts
- Do not enable `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` in
  multi-tenant production without a redaction layer upstream

See `langchain-security-basics` for the redaction middleware pattern.

## Cost

Hybrid doubles observability cost. LangSmith charges per trace; OTEL
backends (Tempo, Datadog APM, New Relic) charge per span or ingest byte.

Before committing to hybrid: estimate cost of both. For many teams, LangSmith
alone on <100k runs/month is cheaper than adding OTEL APM coverage for LLM
spans.

## Migration path

Going from LangSmith-only to OTEL+LangSmith:

1. Install `opentelemetry-sdk`, `opentelemetry-exporter-*`, and
   `opentelemetry-instrumentation-langchain` (or equivalent wrapper)
2. Keep LangSmith env vars unchanged
3. Start with OTEL collecting HTTP + DB only; do NOT enable LangChain
   instrumentation yet
4. Verify no double-emission on LLM metrics
5. Enable LangChain instrumentation if you actually need OTEL spans for LLM
   (most teams do not — LangSmith covers it)

Going from OTEL-only to OTEL+LangSmith:

1. Enable `LANGSMITH_TRACING=true` with a fresh project per env
2. Set Pattern A trace-ID correlation (above)
3. Route eval/annotation work to LangSmith; keep alerts on Prometheus/OTEL

## References

- `langchain-otel-observability` (L33) — deep OTEL integration, out of scope here
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [LangSmith tracing](https://docs.smith.langchain.com/observability/concepts)
- Pack pain catalog: P27 (OTEL prompt content default), P28 (callback propagation)
