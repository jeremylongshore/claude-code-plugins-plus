# langchain-otel-observability — One-Pager

Wire LangChain 1.0 / LangGraph 1.0 traces into OpenTelemetry-native backends (Jaeger, Honeycomb, Grafana Tempo, Datadog) with LLM-specific SLOs, safe prompt-content policy, and subgraph-aware span propagation.

## The Problem

An engineer wires OTEL expecting to see prompts and responses in Honeycomb; only timing, model name, and token counts appear — the prompt body is blank (P27). This is a privacy-safe default: `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` is off. Flipping it on in a multi-tenant workload leaks Tenant A's PII into Tenant B's traces the instant an engineer searches them. Meanwhile, a `BaseCallbackHandler` attached to the parent runnable never fires on inner agent tool calls because LangGraph creates a child runtime per subgraph and callbacks do not inherit (P28) — subagent spans appear orphaned in the waterfall, or they do not appear at all, and your SLO dashboards under-count latency on the exact calls that matter most.

## The Solution

This skill walks through OTEL exporter setup for four backends (Jaeger, Honeycomb, Grafana Tempo, Datadog) with per-backend endpoint and sampling config; the OTEL GenAI semantic conventions (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`) that LangChain 1.0 emits natively vs what needs custom instrumentation; a prompt-content policy tying the capture toggle to compliance posture (GDPR, HIPAA, SOC2) with explicit multi-tenant guardrails; subgraph span propagation via `config["callbacks"]` that ensures nested graphs create child spans correctly; LLM SLO definitions (p95 / p99 latency, error rate, cost-per-request, time-to-first-token) with dashboards and burn-rate alerts. Pinned to LangChain 1.0.x and current OTEL GenAI semantic conventions, with four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Platform/SRE engineers and senior backend wiring LangChain into an existing OTEL stack (Jaeger, Honeycomb, Tempo, Datadog). Not for LangSmith-first teams — see `langchain-observability` for that |
| **What** | OTEL exporter install + per-backend setup; GenAI semconv attribute schema; prompt-content policy with multi-tenant guardrail; subgraph callback propagation; LLM SLO dashboards + burn-rate alerts; backend comparison matrix; 4 references |
| **When** | Compliance or architecture rules out LangSmith as sole sink; you already run Jaeger/Honeycomb/Tempo/Datadog for the rest of the stack; you need LLM spans in the same waterfall as DB and HTTP spans for incident forensics |

## Key Features

1. **Backend matrix across four OTEL-native sinks** — Jaeger (self-hosted, free, no cost visualization), Honeycomb (SaaS, BubbleUp on LLM attrs, generous free tier), Grafana Tempo (self-hosted, pairs with Prometheus for cost metrics), Datadog (SaaS, APM integration, expensive at scale); each with endpoint, auth, and sampling knobs
2. **Prompt-content policy with multi-tenant guardrail** — `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` only on trusted single-tenant workloads; in multi-tenant you MUST run redaction middleware upstream (cross-references `langchain-security-basics`); ties capture toggle to GDPR / HIPAA / SOC2 posture
3. **Subgraph-aware span propagation (P28 fix)** — Pass callbacks via `config["callbacks"]` at invocation time, not via `Runnable.with_config()` which binds at definition time; verified pattern for nested LangGraph subagents; failure mode (orphaned spans, under-counted latency) is named and measurable

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
