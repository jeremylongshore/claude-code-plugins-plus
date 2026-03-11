# LangChain Observability - Detailed Implementation

## Prometheus Metrics Callback

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from langchain_core.callbacks import BaseCallbackHandler
import time

LLM_REQUESTS = Counter("langchain_llm_requests_total", "Total LLM requests", ["model", "status"])
LLM_LATENCY = Histogram("langchain_llm_latency_seconds", "LLM request latency", ["model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
LLM_TOKENS = Counter("langchain_llm_tokens_total", "Total tokens processed", ["model", "type"])
ACTIVE_REQUESTS = Gauge("langchain_active_requests", "Currently active LLM requests")

class PrometheusCallback(BaseCallbackHandler):
    def __init__(self):
        self.start_times = {}

    def on_llm_start(self, serialized, prompts, run_id, **kwargs):
        ACTIVE_REQUESTS.inc()
        self.start_times[str(run_id)] = time.time()

    def on_llm_end(self, response, run_id, **kwargs):
        ACTIVE_REQUESTS.dec()
        model = response.llm_output.get("model_name", "unknown") if response.llm_output else "unknown"
        if str(run_id) in self.start_times:
            latency = time.time() - self.start_times.pop(str(run_id))
            LLM_LATENCY.labels(model=model).observe(latency)
        LLM_REQUESTS.labels(model=model, status="success").inc()
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            LLM_TOKENS.labels(model=model, type="input").inc(usage.get("prompt_tokens", 0))
            LLM_TOKENS.labels(model=model, type="output").inc(usage.get("completion_tokens", 0))

    def on_llm_error(self, error, run_id, **kwargs):
        ACTIVE_REQUESTS.dec()
        LLM_REQUESTS.labels(model="unknown", status="error").inc()

start_http_server(9090)
```

## OpenTelemetry Callback

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

class OpenTelemetryCallback(BaseCallbackHandler):
    def __init__(self):
        self.spans = {}

    def on_chain_start(self, serialized, inputs, run_id, **kwargs):
        span = tracer.start_span(
            name=f"chain.{serialized.get('name', 'unknown')}",
            attributes={"langchain.run_id": str(run_id)}
        )
        self.spans[str(run_id)] = span

    def on_chain_end(self, outputs, run_id, **kwargs):
        if str(run_id) in self.spans:
            self.spans.pop(str(run_id)).end()

    def on_llm_start(self, serialized, prompts, run_id, parent_run_id, **kwargs):
        parent_span = self.spans.get(str(parent_run_id))
        context = trace.set_span_in_context(parent_span) if parent_span else None
        span = tracer.start_span(name=f"llm.{serialized.get('name', 'unknown')}", context=context)
        self.spans[str(run_id)] = span

    def on_llm_end(self, response, run_id, **kwargs):
        if str(run_id) in self.spans:
            span = self.spans.pop(str(run_id))
            if response.llm_output and "token_usage" in response.llm_output:
                usage = response.llm_output["token_usage"]
                span.set_attribute("langchain.prompt_tokens", usage.get("prompt_tokens", 0))
                span.set_attribute("langchain.completion_tokens", usage.get("completion_tokens", 0))
            span.end()
```

## Structured Logging Callback

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger()

class StructuredLoggingCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, run_id, **kwargs):
        logger.info("llm_start", run_id=str(run_id), model=serialized.get("name"), prompt_count=len(prompts))

    def on_llm_end(self, response, run_id, **kwargs):
        token_usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
        logger.info("llm_end", run_id=str(run_id), generations=len(response.generations), **token_usage)

    def on_llm_error(self, error, run_id, **kwargs):
        logger.error("llm_error", run_id=str(run_id), error_type=type(error).__name__, error_message=str(error))
```

## Grafana Dashboard JSON

```json
{
  "title": "LangChain Observability",
  "panels": [
    {"title": "Request Rate", "type": "graph", "targets": [{"expr": "rate(langchain_llm_requests_total[5m])", "legendFormat": "{{model}} - {{status}}"}]},
    {"title": "Latency P95", "type": "graph", "targets": [{"expr": "histogram_quantile(0.95, rate(langchain_llm_latency_seconds_bucket[5m]))", "legendFormat": "{{model}}"}]},
    {"title": "Token Usage", "type": "graph", "targets": [{"expr": "rate(langchain_llm_tokens_total[5m])", "legendFormat": "{{model}} - {{type}}"}]},
    {"title": "Error Rate", "type": "singlestat", "targets": [{"expr": "sum(rate(langchain_llm_requests_total{status='error'}[5m])) / sum(rate(langchain_llm_requests_total[5m]))"}]}
  ]
}
```

## Alerting Rules

```yaml
groups:
  - name: langchain
    rules:
      - alert: HighErrorRate
        expr: sum(rate(langchain_llm_requests_total{status="error"}[5m])) / sum(rate(langchain_llm_requests_total[5m])) > 0.05
        for: 5m
        labels: { severity: critical }
        annotations: { summary: "High LLM error rate", description: "Error rate is {{ $value | humanizePercentage }}" }
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(langchain_llm_latency_seconds_bucket[5m])) > 5
        for: 5m
        labels: { severity: warning }
        annotations: { summary: "High LLM latency", description: "P95 latency is {{ $value }}s" }
      - alert: TokenBudgetExceeded
        expr: sum(increase(langchain_llm_tokens_total[1h])) > 1000000
        labels: { severity: warning }
        annotations: { summary: "High token usage" }
```
