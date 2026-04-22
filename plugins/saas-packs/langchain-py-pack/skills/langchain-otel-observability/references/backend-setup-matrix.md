# OTEL Backend Setup Matrix

Four OTEL-native backends where LangChain 1.0 traces can land. Pick one; you can
dual-export during migration. All four speak OTLP (gRPC on 4317, HTTP on 4318),
so the exporter config is a URL swap — the rest of the skill applies unchanged.

## Comparison matrix

| Backend | Hosting | Cost | LLM-specific UX | Sampling default | Best for |
|---------|---------|------|-----------------|------------------|----------|
| **Jaeger** | Self-hosted (Docker, Helm) | Free (infra only) | None — generic span viewer | 100% (configure at SDK) | Dev/staging, on-prem compliance, teams with existing Jaeger |
| **Honeycomb** | SaaS | Free tier 20M events/mo; paid from $130/mo | BubbleUp over `gen_ai.*` attrs; heatmaps of latency per model | Dynamic (head + tail) | Teams wanting fast LLM-specific slicing without building dashboards |
| **Grafana Tempo** | Self-hosted or Grafana Cloud | Tempo free self-hosted; Cloud free tier 50GB | Pairs with Prometheus for cost metrics; TraceQL queries | 10-100% (SDK + collector) | Teams already on Grafana stack wanting unified logs/metrics/traces |
| **Datadog** | SaaS | ~$31/host/mo APM + LLM Observability add-on (priced per trace) | Native LLM Observability product with token cost, eval scores | 100% (Datadog-side tail) | Enterprise teams standardized on Datadog APM |

## Shared: install the OTEL Python SDK

```bash
pip install \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp-proto-http \
  opentelemetry-instrumentation-langchain
```

`opentelemetry-instrumentation-langchain` (from the OpenLLMetry project by
Traceloop) emits OTEL GenAI semantic conventions automatically on every
LangChain / LangGraph invocation. LangChain-core has a built-in OTEL emitter
too; the Traceloop package is currently the richer path and is what the rest
of this skill assumes. Pin `opentelemetry-instrumentation-langchain >= 0.33`.

## Shared: base SDK setup

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

resource = Resource.create({
    "service.name": "my-langchain-app",
    "service.version": "1.0.0",
    "deployment.environment": "prod",
})

provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(endpoint=OTLP_ENDPOINT, headers=OTLP_HEADERS),
    max_queue_size=2048,
    max_export_batch_size=512,
))
trace.set_tracer_provider(provider)

LangchainInstrumentor().instrument()
```

`BatchSpanProcessor` adds well under 1ms per span at the default batch size.
Use `SimpleSpanProcessor` only in dev — it blocks the event loop per span.

---

## Jaeger (self-hosted)

```bash
docker run -d --name jaeger \
  -p 16686:16686 -p 4318:4318 \
  jaegertracing/all-in-one:1.62
```

```python
OTLP_ENDPOINT = "http://localhost:4318/v1/traces"
OTLP_HEADERS = {}
```

UI at `http://localhost:16686`. No LLM-specific view — you get a generic span
waterfall. Query by service name and filter tags like `gen_ai.system=anthropic`.
Free and easy for local dev; for production deploy via the `jaegertracing/jaeger`
Helm chart with Cassandra or Elasticsearch backing storage.

**Sampling:** Jaeger honors the SDK sampler. For high-volume prod (>100 req/s),
set the SDK to `TraceIdRatioBased(0.1)` (10%) to keep storage manageable. See
[LLM SLO Dashboards](llm-slo-dashboards.md) for why head sampling is risky for
tail-latency SLOs and how to compensate.

---

## Honeycomb (SaaS)

```python
import os
OTLP_ENDPOINT = "https://api.honeycomb.io/v1/traces"
OTLP_HEADERS = {
    "x-honeycomb-team": os.environ["HONEYCOMB_API_KEY"],
    "x-honeycomb-dataset": "langchain-prod",
}
```

Honeycomb's **BubbleUp** over `gen_ai.*` attributes is the killer feature: you
select a slow outlier and Honeycomb surfaces which model, which prompt length,
which tool count correlates with slowness — in seconds, no pre-built dashboard
needed. Free tier is 20M events/month; a busy chat app at ~200k req/day and
15 spans/req uses ~90M/month, so budget accordingly.

**Sampling:** Honeycomb has native dynamic sampling (head + tail). Use
`opentelemetry-exporter-otlp` with 100% SDK sampling and configure dynamic
sampling server-side via Refinery if volume requires it.

---

## Grafana Tempo (self-hosted / Grafana Cloud)

```python
# Grafana Cloud
OTLP_ENDPOINT = "https://tempo-prod-XX-prod-us-east-0.grafana.net/otlp/v1/traces"
OTLP_HEADERS = {
    "Authorization": f"Basic {os.environ['GRAFANA_OTLP_TOKEN']}",
}

# Self-hosted Tempo
OTLP_ENDPOINT = "http://tempo.monitoring.svc.cluster.local:4318/v1/traces"
OTLP_HEADERS = {}
```

Tempo stores traces only; for LLM SLO dashboards you emit metrics via
`opentelemetry-exporter-prometheus` alongside, then query in Grafana with
TraceQL for spans + PromQL for metrics. See [LLM SLO Dashboards](llm-slo-dashboards.md)
for the PromQL examples.

**Sampling:** Configure in the SDK or upstream via the OTEL Collector's
`tailsamplingprocessor`. Tail sampling that keeps all spans where
`gen_ai.usage.output_tokens > 1000` OR status is error gives you outlier
coverage without full 100% storage cost.

---

## Datadog (SaaS)

Datadog supports OTLP ingest directly from v7.40+ Agent, or via the Datadog
Collector. LLM Observability is a separate paid add-on that surfaces
LangChain spans with token costs and eval scoring.

```python
OTLP_ENDPOINT = "http://datadog-agent.monitoring.svc.cluster.local:4318/v1/traces"
OTLP_HEADERS = {}
```

The agent forwards to Datadog with the site-specific endpoint baked in. For
Datadog-less setups, use the direct OTLP endpoint:

```python
OTLP_ENDPOINT = "https://trace.agent.datadoghq.com/api/v0.2/traces"
OTLP_HEADERS = {"DD-API-KEY": os.environ["DD_API_KEY"]}
```

**Sampling:** Datadog does tail sampling server-side. Send 100% from SDK; they
sample at ingest. Costs grow quickly with span volume — a busy agent workload
at 1M spans/day can run $500+/month on APM alone, before LLM Observability.

---

## Dual-exporting during migration

To validate a backend swap before cutover, register two processors:

```python
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
provider.add_span_processor(BatchSpanProcessor(honeycomb_exporter))
```

Both exporters see every span. Compare waterfall correctness across backends
for two weeks, then remove the retiring one. Watch the collector's exporter
failure metrics — a silently failing second exporter will look like it's working
in your new backend.

## Sources

- OTEL Python SDK — https://opentelemetry.io/docs/languages/python/
- OpenLLMetry — https://github.com/traceloop/openllmetry
- Jaeger — https://www.jaegertracing.io/docs/1.62/
- Honeycomb OTLP — https://docs.honeycomb.io/getting-data-in/otlp/
- Grafana Tempo — https://grafana.com/docs/tempo/latest/
- Datadog OTLP — https://docs.datadoghq.com/opentelemetry/
