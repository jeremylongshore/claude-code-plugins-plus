# Custom Metrics Callback

The `MetricCallback` in the main skill is the integration point between
LangChain and your metrics stack. This reference fills in the sink adapters
(Prometheus / StatsD / Datadog), deduplication for retried calls (P25), and
common pitfalls.

## Sink protocol

The callback needs two verbs: counter increment and histogram record.

```python
from typing import Protocol

class MetricSink(Protocol):
    def incr(self, name: str, value: float, tags: dict[str, str]) -> None: ...
    def hist(self, name: str, value: float, tags: dict[str, str]) -> None: ...
```

Callback construction stays the same across sinks; only the sink adapter
changes. This means test coverage uses an `InMemorySink` and production
swaps in Prometheus / StatsD / Datadog by DI.

## Prometheus sink (pull model)

```python
from prometheus_client import Counter, Histogram, start_http_server

_TOKEN_IN = Counter("llm_token_in_total",  "Input tokens",  ["tenant_id", "model"])
_TOKEN_OUT = Counter("llm_token_out_total", "Output tokens", ["tenant_id", "model"])
_LATENCY  = Histogram("llm_latency_ms",     "LLM call latency (ms)",
                      ["tenant_id", "model"],
                      buckets=(10, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000))
_ERRORS   = Counter("llm_errors_total",     "LLM errors",
                    ["tenant_id", "model", "error_type"])

class PrometheusSink:
    """Exports on /metrics; scrape with a Prometheus server."""

    _METRICS = {
        "llm.token_in":   _TOKEN_IN,
        "llm.token_out":  _TOKEN_OUT,
        "llm.error":      _ERRORS,
    }
    _HISTS = {"llm.latency_ms": _LATENCY}

    def incr(self, name: str, value: float, tags: dict[str, str]) -> None:
        if name in self._METRICS:
            self._METRICS[name].labels(**tags).inc(value)

    def hist(self, name: str, value: float, tags: dict[str, str]) -> None:
        if name in self._HISTS:
            self._HISTS[name].labels(**tags).observe(value)

# Start the /metrics endpoint once at process startup:
# start_http_server(9090)
```

**Cardinality warning:** Prometheus labels are stored per unique combination.
If `tenant_id` has 10k+ values, use a tier bucket (`tier:enterprise`,
`tier:starter`) in Prometheus and keep the full tenant_id in LangSmith metadata
only. Time-series DB cardinality is the #2 cost driver after LLM spend in
most SaaS deployments.

## StatsD sink (push model)

```python
from datadog import DogStatsd  # works without Datadog — uses StatsD protocol

class StatsDSink:
    def __init__(self, host: str = "localhost", port: int = 8125) -> None:
        self.client = DogStatsd(host=host, port=port, namespace="llm")

    def incr(self, name: str, value: float, tags: dict[str, str]) -> None:
        self.client.increment(
            name.removeprefix("llm."),
            value=value,
            tags=[f"{k}:{v}" for k, v in tags.items()],
        )

    def hist(self, name: str, value: float, tags: dict[str, str]) -> None:
        self.client.histogram(
            name.removeprefix("llm."),
            value=value,
            tags=[f"{k}:{v}" for k, v in tags.items()],
        )
```

StatsD is UDP fire-and-forget — zero backpressure, zero exceptions on
the hot path. Safe default for high-throughput services.

## Datadog sink

Use Datadog APM alongside the callback when you want both metrics and spans:

```python
from ddtrace import tracer
from datadog import DogStatsd

class DatadogSink:
    """Metrics via statsd + spans via ddtrace. Use ddtrace auto-instrumentation
    for HTTP/DB spans; the callback supplies the LLM-specific span details.
    """

    def __init__(self) -> None:
        self.statsd = DogStatsd(namespace="llm")

    def incr(self, name: str, value: float, tags: dict[str, str]) -> None:
        self.statsd.increment(name.removeprefix("llm."), value=value,
                              tags=[f"{k}:{v}" for k, v in tags.items()])
        # Also tag the active span
        span = tracer.current_span()
        if span is not None:
            span.set_tag(name.replace(".", "_"), value)
            for k, v in tags.items():
                span.set_tag(k, v)

    def hist(self, name: str, value: float, tags: dict[str, str]) -> None:
        self.statsd.histogram(name.removeprefix("llm."), value=value,
                              tags=[f"{k}:{v}" for k, v in tags.items()])
```

For OTEL-native tracing (spans, not just metrics) defer to
`langchain-otel-observability` (L33) — do not roll your own.

## Dedupe retries (P25)

When retry middleware runs a model call twice, both emit `on_llm_end`. Naive
aggregation double-counts tokens. Dedupe by LangChain's `run_id`:

```python
class MetricCallback(BaseCallbackHandler):
    def __init__(self, tenant_id: str, sink: MetricSink) -> None:
        self.tenant_id = tenant_id
        self.sink = sink
        self._starts: dict[str, float] = {}
        self._seen: set[str] = set()   # run_ids already emitted

    def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        run_key = str(run_id)
        if run_key in self._seen:
            return                     # retry duplicate — ignore
        self._seen.add(run_key)
        # ... rest of normal logic
```

Alternative: place token accounting *above* the retry middleware in the chain
so it only sees the final successful call. See P25 in `docs/pain-catalog.md`.

## Latency: capture in `on_llm_start`, not `on_chat_model_start`

`on_chat_model_start` fires after message formatting; `on_llm_start` fires at
actual provider call. On streaming, use `on_llm_end` as end-of-stream; the
Anthropic `usage_metadata` is populated at stream close (P01), but your
latency number should reflect wall-clock, not token-count time.

## Async variants

`BaseCallbackHandler.on_llm_*` are sync. For async workloads use
`AsyncCallbackHandler`:

```python
from langchain_core.callbacks import AsyncCallbackHandler

class AsyncMetricCallback(AsyncCallbackHandler):
    async def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        # same logic, but await async sinks
        ...
```

Mix sync/async sinks carefully — blocking sync sink in an async callback
freezes the event loop. Use StatsD (UDP, non-blocking) or queue-based sinks
in async services.

## Testing

```python
class InMemorySink:
    def __init__(self) -> None:
        self.counters: dict[str, float] = {}
        self.hists: list[tuple[str, float, dict]] = []

    def incr(self, name, value, tags):
        self.counters[name] = self.counters.get(name, 0) + value

    def hist(self, name, value, tags):
        self.hists.append((name, value, tags))

def test_callback_counts_tokens():
    sink = InMemorySink()
    cb = MetricCallback("acme", sink)
    # drive through a `FakeListChatModel` with `generation_info={"token_usage": {...}}`
    # see P43 in pack pain-catalog for FakeListChatModel caveat
    ...
    assert sink.counters["llm.token_out"] > 0
```

## References

- [`BaseCallbackHandler` API](https://python.langchain.com/api_reference/core/callbacks/langchain_core.callbacks.base.BaseCallbackHandler.html)
- [`AsyncCallbackHandler` API](https://python.langchain.com/api_reference/core/callbacks/langchain_core.callbacks.base.AsyncCallbackHandler.html)
- [prometheus_client Python](https://prometheus.github.io/client_python/)
- Pack pain catalog: P25 (retry double-count), P28 (invocation-time propagation)
