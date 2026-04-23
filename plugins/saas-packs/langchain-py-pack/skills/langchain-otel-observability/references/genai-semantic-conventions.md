# OTEL GenAI Semantic Conventions for LangChain

The OpenTelemetry **GenAI semantic conventions** define a standard attribute
schema for LLM spans so that backends can render model, token, and cost
information uniformly. LangChain 1.0 via `opentelemetry-instrumentation-langchain`
emits most of these natively; a handful require custom instrumentation.

Spec: https://opentelemetry.io/docs/specs/semconv/gen-ai/

## Attribute schema (what LangChain emits)

### Required on every LLM span

| Attribute | Type | Example | Emitted by LangChain 1.0 |
|-----------|------|---------|--------------------------|
| `gen_ai.system` | string | `anthropic`, `openai`, `google.gemini`, `cohere` | Yes — auto-detected from provider class |
| `gen_ai.operation.name` | string | `chat`, `text_completion`, `embeddings` | Yes |
| `gen_ai.request.model` | string | `claude-sonnet-4-6`, `gpt-4o` | Yes — from `model` kwarg |

### Request parameters

| Attribute | Type | Example | Emitted by LangChain 1.0 |
|-----------|------|---------|--------------------------|
| `gen_ai.request.temperature` | double | `0.7` | Yes |
| `gen_ai.request.top_p` | double | `0.95` | Yes |
| `gen_ai.request.max_tokens` | int | `4096` | Yes |
| `gen_ai.request.frequency_penalty` | double | `0.0` | OpenAI only |
| `gen_ai.request.presence_penalty` | double | `0.0` | OpenAI only |
| `gen_ai.request.stop_sequences` | string[] | `["\\n\\nHuman:"]` | Yes |

### Response metadata

| Attribute | Type | Example | Emitted by LangChain 1.0 |
|-----------|------|---------|--------------------------|
| `gen_ai.response.model` | string | `claude-sonnet-4-6-20250514` | Yes |
| `gen_ai.response.id` | string | `msg_01Abc...` | Yes |
| `gen_ai.response.finish_reasons` | string[] | `["stop", "tool_calls"]` | Yes |

### Token usage

| Attribute | Type | Example | Emitted by LangChain 1.0 |
|-----------|------|---------|--------------------------|
| `gen_ai.usage.input_tokens` | int | `1234` | Yes |
| `gen_ai.usage.output_tokens` | int | `567` | Yes |
| `gen_ai.usage.cache_read_input_tokens` | int | `100` | Anthropic only — needs aggregation (see P04) |
| `gen_ai.usage.cache_creation_input_tokens` | int | `50` | Anthropic only |
| `gen_ai.usage.reasoning_tokens` | int | `89` | OpenAI o1 series only |

### Prompt / completion content (opt-in, see prompt-content-policy.md)

| Attribute | Type | Emitted when `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` |
|-----------|------|--------|
| `gen_ai.prompt.<n>.role` | string | `system`, `user`, `assistant`, `tool` |
| `gen_ai.prompt.<n>.content` | string | **PII / PHI risk — see policy** |
| `gen_ai.completion.<n>.role` | string | `assistant` |
| `gen_ai.completion.<n>.content` | string | **PII / PHI risk** |
| `gen_ai.completion.<n>.finish_reason` | string | `stop`, `length`, `tool_calls` |

## LangChain span taxonomy

`opentelemetry-instrumentation-langchain` creates spans on every `Runnable`.
Span names follow `<component>.<method>` conventions:

| Span name | Component | Extra attributes |
|-----------|-----------|------------------|
| `ChatAnthropic.chat` / `ChatOpenAI.chat` | Chat model | All `gen_ai.*` above |
| `Runnable.invoke` / `Runnable.stream` | LCEL wrapper | `langchain.runnable.name` |
| `Tool.<name>` | Tool invocation | `gen_ai.tool.name`, `gen_ai.tool.call_id`, `gen_ai.tool.arguments` (if content capture on) |
| `Retriever.get_relevant_documents` | Retriever | `langchain.retriever.source`, `langchain.retriever.k` |
| `VectorStore.similarity_search` | Vector store | `db.system` (e.g. `pinecone`, `chroma`), `db.operation` |
| `ChatPromptTemplate.format_messages` | Prompt template | `langchain.prompt.template_format` (`f-string` / `jinja2`) |

### LangGraph spans

LangGraph adds a parent-child relationship per node:

| Span name | Parent | When |
|-----------|--------|------|
| `LangGraph.invoke` | Root | Every graph invocation |
| `LangGraph.node.<node_name>` | `LangGraph.invoke` | Each node execution |
| `LangGraph.subgraph.<subgraph_name>` | `LangGraph.node.*` | Each subgraph call |
| Model / tool spans | `LangGraph.node.*` | Nested under the node that called them |

**P28 failure mode:** If callbacks are not propagated via `config["callbacks"]`,
spans inside subgraphs are **not** children of `LangGraph.subgraph.*`. They
either do not appear or appear as orphaned root spans. See SKILL.md Step 4.

## What's missing and needs custom instrumentation

LangChain 1.0 does not emit these natively. If you need them, add a
`BaseCallbackHandler` that sets them in `on_llm_end`:

1. **Cost** — `gen_ai.usage.cost_usd` (custom attribute, not yet standardized).
   Calculate from `input_tokens * input_price + output_tokens * output_price`.
2. **TTFT (time to first token)** — emit a span event `first_token` inside
   `on_llm_new_token`. Backends (Honeycomb, Datadog) can query the delta from
   span start.
3. **Evaluation scores** — if you run an LLM-as-judge post-hoc, attach
   `gen_ai.evaluation.<metric>` attributes on the original span via span
   links rather than overwriting.

### Cost attribute example

```python
from langchain_core.callbacks import BaseCallbackHandler
from opentelemetry import trace

PRICING = {  # USD per 1M tokens; keep in sync with provider pricing pages
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

class CostAttributeHandler(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        span = trace.get_current_span()
        if not span.is_recording():
            return
        model = kwargs.get("invocation_params", {}).get("model", "")
        usage = response.llm_output.get("token_usage", {})
        price = PRICING.get(model)
        if not price:
            return
        cost = (
            usage.get("prompt_tokens", 0) * price["input"] / 1_000_000
            + usage.get("completion_tokens", 0) * price["output"] / 1_000_000
        )
        span.set_attribute("gen_ai.usage.cost_usd", cost)
```

Attach to every invocation via `config["callbacks"]=[CostAttributeHandler()]`
(do not use `.with_config()` — P28).

## Attribute hygiene

- Keep attribute values under 1KB. Spans with huge strings balloon backend
  storage costs and trigger exporter drops.
- Never put user IDs in free-form attributes — use `enduser.id` (standard
  OTEL resource attribute) so RBAC / redaction rules can target it.
- Session / thread ID from LangGraph should map to `session.id` (standard
  attribute) so traces from the same conversation cluster in the UI.

## Sources

- OTEL GenAI conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/
- OTEL resource conventions — https://opentelemetry.io/docs/specs/semconv/resource/
- OpenLLMetry LangChain instrumentation — https://github.com/traceloop/openllmetry/tree/main/packages/opentelemetry-instrumentation-langchain
