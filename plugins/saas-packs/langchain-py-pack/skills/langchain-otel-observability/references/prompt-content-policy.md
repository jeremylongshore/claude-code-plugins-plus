# Prompt-Content Policy for OTEL Traces

OTEL GenAI's privacy-safe default (P27) is that prompt and completion bodies are
**not** exported. The engineer's instinct on day one is to flip
`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` and move on — and this
is the single most common data-exfiltration risk when adding observability to
an LLM service.

This reference is the decision framework: when is capture safe, when is it
actually dangerous, and how to wire redaction upstream.

## The default (what you get without any config)

```
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT  (unset or "false")
```

Trace attributes present:
- `gen_ai.system`, `gen_ai.request.model`, `gen_ai.response.id`
- `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`
- Request params (temperature, max_tokens, stop_sequences)
- `gen_ai.response.finish_reasons`
- Tool names (but not arguments)

Trace attributes **missing**:
- `gen_ai.prompt.<n>.content`
- `gen_ai.completion.<n>.content`
- `gen_ai.tool.arguments`

For latency + cost + error-rate dashboards this is sufficient. Turn capture on
only if you have a concrete reason the bodies are needed.

## When capture is safe

Single-tenant, trusted-operator workloads with one or more of:

1. **Internal-only service** with no end-user data flowing through prompts —
   for example an agent that operates on your public corpus.
2. **Dev / staging environment** with synthetic or scrubbed inputs. Never copy
   staging traces into prod backends where search rules differ.
3. **SaaS product with explicit user consent** (in ToS) to trace for support;
   the backend has RBAC so only on-call engineers can view; automatic retention
   of ≤14 days; tenant-scoped redaction already applied upstream by middleware.
4. **Regulated workload with legal blessing** — e.g. HIPAA BAA in place with
   backend vendor, signed DPIA for GDPR, documented SOC2 controls mapping the
   trace store to the same severity as application logs.

## When capture is dangerous

Any of these makes `CAPTURE_MESSAGE_CONTENT=true` a breach waiting to happen:

1. **Multi-tenant without upstream redaction** — Tenant A's prompt lands in a
   span that Tenant A's customer-success engineer queries; the engineer is
   inside Tenant B's account context; you just leaked B's data into A's ticket.
2. **Healthcare, finance, legal prompts** without explicit BAA / DPIA and a
   trace backend that meets the corresponding control framework.
3. **Prompts that contain pasted secrets** — users paste API keys, connection
   strings, private keys into chat assistants constantly. Capture-on means
   those land in your trace store forever (retention typically ≥30 days).
4. **Shared-developer backend** where debugging engineers from many products
   can query across datasets — one engineer's SELECT is another product's
   compliance incident.

## The guardrail: redact-before-observe

The correct architecture:

```
User input
   → redaction middleware  (strip PII/PHI, replace secrets with placeholders)
   → cache middleware      (hash the redacted text, not raw)
   → chat model            (prompt with redacted content)
   → OTEL span             (captures the already-redacted content — safe)
```

Redaction must happen **upstream of the model call** so the span, which
instruments the model call, only sees redacted content. Cross-reference
`langchain-security-basics` (redaction middleware patterns, P34 cross-ref) and
`langchain-middleware-patterns` (middleware order; redact → cache → model).

### Minimal redaction middleware sketch

```python
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage
import re

PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"sk-[A-Za-z0-9]{32,}"), "[API_KEY]"),
    (re.compile(r"sk-ant-[A-Za-z0-9-]{32,}"), "[ANTHROPIC_KEY]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    # Add patterns for your domain — credit cards, phone, addresses, IDs.
]

def redact_text(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

def redact_messages(msgs: list) -> list:
    redacted = []
    for m in msgs:
        if isinstance(m, (HumanMessage, AIMessage)) and isinstance(m.content, str):
            redacted.append(type(m)(content=redact_text(m.content)))
        else:
            redacted.append(m)
    return redacted

redact = RunnableLambda(redact_messages)
chain = redact | prompt | llm
```

For production, use a named-entity recognition (NER) service — `presidio-analyzer`
is open source, or a commercial DLP (AWS Macie, GCP DLP). Regex-only redaction
misses a lot.

## Environment variable matrix

Set per-environment, not per-process. The exporter reads env at init.

| Env var | Value | Effect |
|---------|-------|--------|
| (unset) | — | Default: no content in traces |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `false` | Explicit: no content |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `true` | Capture prompt + completion content |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `NO_CONTENT` | Alias for false (some versions) |
| `TRACELOOP_TRACE_CONTENT` | `false` | OpenLLMetry-specific alias; either knob works |

Verify which knob your version honors — OpenLLMetry releases have changed the
primary knob name. Set both to be safe.

## Compliance posture mapping

| Framework | Policy |
|-----------|--------|
| **GDPR** | Prompt body may contain personal data. Without a documented lawful basis, keep content capture off in production. If on, document retention, subject-access workflow, and DPIA. |
| **HIPAA** | Prompts may contain PHI. Require a BAA with the trace backend vendor; same vendor can store logs but not always traces — verify. Off by default; turn on only with legal sign-off. |
| **SOC2** | Trace store counts as a system containing customer data — it must appear in your data-flow diagram and access-control matrix. Off by default; turn on behind RBAC. |
| **PCI-DSS** | Card data in prompts must never enter the trace store. Mandatory upstream redaction; fail closed (crash the request) if the redactor is down. |
| **Internal-only / no regulated data** | On is fine. Document the decision. |

## Audit pattern

Run a periodic sampler that checks 0.1% of recent trace spans for regex hits on
raw PII patterns (SSN, credit card, API key prefix). If any fire, your
redactor has a gap. This is an O(1) ops task with a cron + Honeycomb/Datadog
query; the pattern pays for itself the first time it catches a leak.

## Sources

- OTEL GenAI semconv — content capture flag — https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Presidio (open-source PII detection) — https://microsoft.github.io/presidio/
- OpenLLMetry capture toggle — https://www.traceloop.com/docs/openllmetry/privacy
- Pack cross-reference — `langchain-security-basics`, `langchain-middleware-patterns`
- Pain catalog — P27 (default-off), P34 (prompt injection), P37 (secrets hygiene)
