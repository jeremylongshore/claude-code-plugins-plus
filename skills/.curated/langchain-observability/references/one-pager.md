# langchain-observability — One-Pager

Wire LangSmith tracing and custom metric callbacks into a LangChain 1.0 / LangGraph 1.0 service without losing traces to an env-var typo or losing subgraph metrics to callback-scoping.

## The Problem

An engineer sets `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY=...`, restarts the service, and sees no traces in LangSmith. The 1.0 canonical spelling is `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` — the legacy `LANGCHAIN_*` names are soft-deprecated and fail silently on some middleware chains. Once tracing is on, a `BaseCallbackHandler` attached via `Runnable.with_config(callbacks=[...])` fires on the parent runnable but is completely silent on inner LangGraph subgraphs and `create_react_agent` tool calls — because LangGraph creates a child runtime per subgraph and bound callbacks do not propagate. Result: per-tenant cost dashboards under-count by 30-70% on real agent traffic.

## The Solution

This skill pins the canonical 1.0 env vars (`LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`) with a legacy fallback note; supplies a metric-callback template that records `token_in` / `token_out` / `latency_ms` / `tool_calls` / `error` with a `tenant_id` dimension; teaches the `config["callbacks"]` invocation-time pattern that actually propagates to subgraphs (P28); and provides a decision tree for LangSmith-only, OTEL-only, hybrid, and custom-sink setups. Includes trace-tagging via `RunnableConfig` for per-request `tags` and `metadata`, sampling patterns, and a cross-reference to `langchain-otel-observability` (L33) for OTEL-native work.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers wiring day-to-day observability into a LangChain 1.0 / LangGraph 1.0 service — SRE, platform, or application engineers responsible for traces, metrics, and per-tenant cost |
| **What** | Canonical LangSmith env-var setup, `BaseCallbackHandler` metric template (Prometheus/StatsD/Datadog), invocation-time `config["callbacks"]` propagation, trace tagging via `RunnableConfig`, observability-stack decision tree, 4 references (langsmith-setup, custom-metrics-callback, trace-metadata-and-tagging, hybrid-langsmith-otel) |
| **When** | Stand up observability on a new service, debug blank traces in LangSmith, add per-tenant cost breakdowns, or decide between LangSmith-only vs OTEL-native (defer to `langchain-otel-observability` for heavy OTEL work) |

## Key Features

1. **Canonical LangSmith env-var triplet with legacy fallback** — `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY=...` + `LANGSMITH_PROJECT=my-service-prod` is the 1.0 spelling; `LANGCHAIN_TRACING_V2` still works but is deprecated and the source of the single most common "traces missing" incident (P26). Zero-code activation, less than 5ms per-span overhead
2. **Metric-callback template with tenant dimensions** — Drop-in `BaseCallbackHandler` subclass that records `token_in`, `token_out`, `latency_ms`, `tool_calls`, and `error` with a `tenant_id` label, sinking to Prometheus, StatsD, or Datadog; adds under 1ms per callback firing
3. **Invocation-time propagation pattern** — Pass callbacks via `config["callbacks"]` at `invoke()`/`ainvoke()`/`astream()` time so they propagate to LangGraph subgraphs and `create_react_agent` inner tool calls — not via `.with_config(callbacks=[...])` which binds at definition time and never fires inside a subgraph (P28)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
