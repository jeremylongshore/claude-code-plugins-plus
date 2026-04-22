# LangChain Python Skill Pack (v2.0)

> Pain-first Claude Code skills for LangChain 1.0 and LangGraph 1.0 in Python.
> Every skill opens with a specific production failure mode — not capability prose.

## Why This Pack Exists

LangChain 1.0 and LangGraph 1.0 shipped October 2025 with a new middleware model,
typed content blocks (text/tool_use/image), stable checkpointing, first-class
human-in-the-loop interrupts, three streaming modes, and native OpenTelemetry export.
Token accounting, structured output, agent control flow, and memory all behave
differently than they did in the 0.2 / 0.3 era.

This pack replaces the legacy `langchain-pack` with **pain-first, Python-native** skills.
Every skill opens with a specific failure mode — a real exception, a hardcoded threshold,
a version-specific regression — not capability prose:

> `ChatAnthropic.stream()` blocks `llmOutput` token counts until the stream completes.
> Live cost dashboards built on that field lag by `stream_duration` seconds —
> sometimes by 20+ seconds on long responses. Use `astream_events(version="v2")`
> or a callback handler to read tokens incrementally.

See [`docs/pain-catalog.md`](docs/pain-catalog.md) for the full 68-entry catalog of
LangChain 1.0 pain points that every skill in this pack anchors to.

## Installation

```bash
/plugin install langchain-py-pack@claude-code-plugins-plus
```

## TypeScript Counterpart

For LangChain.js + `@langchain/langgraph` in Node 22+ / Vercel / Cloud Run:
`langchain-ts-pack` (Epic B — not yet shipped). Same 34-skill taxonomy, JS-native.

## What Is Shipped Today

| Skill | What it covers |
|-------|-------------|
| `langchain-model-inference` | `ChatAnthropic` / `ChatOpenAI` / `ChatGoogleGenerativeAI` init, content-block iteration, streaming token accounting, structured-output method decision tree — with 4 deep references |
| `langchain-embeddings-search` | `FAISS` vs `Pinecone` flipped score semantics, dim-mismatch prevention, language-aware chunking, hybrid BM25 + vector, reranker filter-by-rank — with 3 deep references |

Both skills are gold-standard quality (≥200 lines each, 3-4 references per skill,
every example pinned to `langchain-core 1.0.x`, A-grade at the 100-point rubric).

## Roadmap — 32 More Skills Landing Across Four Epics

Each epic is one PR. Every skill follows the same gold-standard quality bar as
the two shipped above: concrete pain in the Overview, ≥2 error codes named,
2-4 references, decision trees / comparison tables where applicable, and every
code block pinned to LangChain 1.0.x.

### Epic A2 — Getting Started + Core Workflows (S01-S08 minus the two shipped)

| Code | Skill | Description |
|---|---|---|
| S01 | `langchain-install-auth` | Install `langchain`, `langchain-core`, provider packages; env var management; verify connectivity |
| S02 | `langchain-hello-world` | Minimal `ChatAnthropic` chain with `with_structured_output()`, streaming, and token counting |
| S04 | `langchain-common-errors` | 12+ real error codes with exact fixes (`OutputParserException`, `RateLimitError`, `GraphRecursionError`, agent-loop timeouts) |
| S05 | `langchain-sdk-patterns` | `RunnableSequence`, `.with_fallbacks()`, `.batch()`, `.abatch()`, retries, concurrency caps |
| S06 | `langchain-core-workflow` | `RunnableParallel`, `RunnableBranch`, `RunnablePassthrough.assign()`, RAG composition |
| S08 | `langchain-data-handling` | Document loaders, `RecursiveCharacterTextSplitter`, semantic vs fixed chunking |

### Epic A3 — Operations + Pro (S09-P20)

| Code | Skill | Description |
|---|---|---|
| S09 | `langchain-observability` | LangSmith zero-code tracing, OTEL native export, custom metric callbacks |
| S10 | `langchain-debug-bundle` | `astream_events(version="v2")`, trace callbacks, LangSmith export, diagnostic dump |
| S11 | `langchain-incident-runbook` | LLM-specific SLOs, p95 latency triage, provider outage runbook, cost-overrun response |
| S12 | `langchain-prod-checklist` | 30-item go-live checklist with concrete thresholds |
| S13 | `langchain-ci-integration` | GitHub Actions, `FakeListChatModel`, test gates, dry-run validators |
| S14 | `langchain-deploy-integration` | LangServe, Cloud Run, Vercel Python runtime, secret management |
| P15 | `langchain-performance-tuning` | Streaming modes, batch concurrency, semantic caching, RedisChatMessageHistory |
| P16 | `langchain-cost-tuning` | Real token accounting, model tiering, cache hit rates, per-tenant budgets |
| P17 | `langchain-rate-limits` | `asyncio.Semaphore`, token-bucket, exponential backoff, provider-specific limits |
| P18 | `langchain-security-basics` | Prompt injection defenses, tool allowlisting, PII redaction, output validation |
| P19 | `langchain-enterprise-rbac` | Tenant isolation, per-tenant rate limits, role-scoped retrievers, audit logs |
| P20 | `langchain-multi-env-setup` | Pydantic `Settings` env validation, dev/staging/prod isolation, secret backends |

### Epic A4 — Flagship + LangGraph v1.0 (F21-L34)

| Code | Skill | Description |
|---|---|---|
| F21 | `langchain-reference-architecture` | Layered design, LLM factory, chain registry, DI, tenant-scoped vector stores |
| F22 | `langchain-webhooks-events` | Async callback handlers, SSE streaming, WebSocket, background dispatch |
| F23 | `langchain-local-dev-loop` | `pytest`, `FakeListChatModel`, VCR fixtures, integration-test gating |
| F24 | `langchain-upgrade-migration` | 0.2 → 0.3 → 1.0 migration with named breaking changes, codemod hints |
| L25 | `langchain-langgraph-basics` | `StateGraph`, typed `TypedDict` state, nodes, edges, `compile()`, recursion limits |
| L26 | `langchain-langgraph-agents` | `create_react_agent`, prebuilt tool-calling, `tools_condition`, agent loop caps |
| L27 | `langchain-langgraph-checkpointing` | `MemorySaver`, `PostgresSaver`, `thread_id` semantics, time-travel |
| L28 | `langchain-langgraph-human-in-loop` | `interrupt_before`, `interrupt_after`, `Command(resume=...)`, approval flows |
| L29 | `langchain-langgraph-streaming` | `stream_mode` `"messages"` vs `"updates"` vs `"values"`, token-level streaming |
| L30 | `langchain-langgraph-subgraphs` | Composing graphs, nested agent teams, shared state, subgraph boundaries |
| L31 | `langchain-middleware-patterns` | 1.0 middleware model, PII redaction, caching, retry middleware, ordering rules |
| L32 | `langchain-deep-agents` | Deep Agents: planner + subagents + virtual filesystem + reflection loop |
| L33 | `langchain-otel-observability` | Native OTEL export, Jaeger/Honeycomb, LLM-specific SLO dashboards |
| L34 | `langchain-content-blocks` | Typed `AIMessage.content`, Claude `tool_use` iteration quirks |

## Quick Start

### 1. Install the pack

```bash
/plugin install langchain-py-pack@claude-code-plugins-plus
```

### 2. Install LangChain 1.0 + LangGraph 1.0

```bash
python -m venv .venv && source .venv/bin/activate

pip install "langchain>=1.0,<2.0" "langchain-core>=1.0,<2.0" \
            "langchain-anthropic>=1.0,<2.0" \
            "langgraph>=1.0,<2.0"
```

### 3. A minimal agent with memory

```python
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

agent = create_react_agent(
    model=llm,
    tools=[add],
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "demo-1"}}
result = agent.invoke(
    {"messages": [("user", "What is 17 + 25?")]},
    config=config,
)
print(result["messages"][-1].content)
```

## Key LangChain 1.0 / LangGraph 1.0 Links

- [LangChain 1.0 release notes](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [LangChain Python docs](https://python.langchain.com/docs/)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph streaming modes](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- [`astream_events` v2](https://python.langchain.com/docs/how_to/streaming/#using-stream-events)
- [Checkpointing and persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Human-in-the-loop patterns](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [LangSmith](https://smith.langchain.com)
- [State of Agent Engineering 2026](https://www.langchain.com/state-of-agent-engineering)

## Version Baseline

Every skill in this pack is pinned to `langchain-core 1.0.x` / `langgraph 1.0.x`.
If you are on 0.2.x or 0.3.x, wait for `langchain-upgrade-migration` (Epic A4)
or consult the [legacy `langchain-pack`](../langchain-pack/) in the meantime.

## License

MIT
