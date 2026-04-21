# LangChain Python Skill Pack (v2.0)

> 34 production-grade Claude Code skills for building LLM applications with LangChain 1.0 and LangGraph 1.0 in Python. Covers middleware, checkpointing, human-in-the-loop, streaming modes, Deep Agents, typed content blocks, and the real failure modes you hit in production.

## Why This Pack Exists

LangChain 1.0 and LangGraph 1.0 shipped October 2025 with a new middleware model,
typed content blocks (text/tool_use/image), stable checkpointing, first-class
human-in-the-loop interrupts, three streaming modes, and native OpenTelemetry export.
The ecosystem has changed — token accounting, structured output, agent control flow,
and memory all behave differently than they did in the 0.2 / 0.3 era.

This pack replaces the legacy `langchain-pack` with **pain-first, Python-native** skills.
Every skill opens with a specific failure mode (a real exception, a hardcoded threshold,
a version-specific regression) — not capability prose. No "LCEL lets you pipe chains." Instead:

> `ChatAnthropic.stream()` blocks `llmOutput` token counts until the stream completes.
> Live cost dashboards built on that field lag by `stream_duration` seconds —
> sometimes by 20+ seconds on long responses. Use `astream_events(version="v2")`
> or a callback handler to read tokens incrementally.

See [`docs/pain-catalog.md`](docs/pain-catalog.md) for the full catalog of
LangChain 1.0 pain points that anchor every skill in this pack.

## Installation

```bash
/plugin install langchain-py-pack@claude-code-plugins-plus
```

## TypeScript Counterpart

For LangChain.js + `@langchain/langgraph` in Node 22+ / Vercel / Cloud Run:
install [`langchain-ts-pack`](../langchain-ts-pack/). Same 34-skill taxonomy, JS-native.

## Skills Included

### Getting Started (S01-S04)

| Skill | Description |
|-------|-------------|
| `langchain-install-auth` | Install `langchain`, `langchain-core`, provider packages; env var management; verify connectivity |
| `langchain-hello-world` | Minimal ChatAnthropic chain with `with_structured_output()`, streaming, and token counting |
| `langchain-model-inference` | `ChatAnthropic`, `ChatOpenAI`, model routing, typed content blocks, token accounting quirks |
| `langchain-common-errors` | 12+ real error codes with exact fixes: `OutputParserException`, `RateLimitError`, `GraphRecursionError`, agent-loop timeouts |

### Core Workflows (S05-S08)

| Skill | Description |
|-------|-------------|
| `langchain-sdk-patterns` | `RunnableSequence`, `.with_fallbacks()`, `.batch()`, `.abatch()`, retries, concurrency caps |
| `langchain-core-workflow` | `RunnableParallel`, `RunnableBranch`, `RunnablePassthrough.assign()`, RAG composition |
| `langchain-embeddings-search` | `FaissStore` vs `PineconeStore`, flipped score semantics, hybrid search, rerankers |
| `langchain-data-handling` | Document loaders, `RecursiveCharacterTextSplitter`, semantic vs fixed chunking |

### Operations (S09-S14)

| Skill | Description |
|-------|-------------|
| `langchain-observability` | LangSmith zero-code tracing, OTEL native export, custom metric callbacks |
| `langchain-debug-bundle` | `astream_events(version="v2")`, trace callbacks, LangSmith export, diagnostic dump |
| `langchain-incident-runbook` | LLM-specific SLOs, p95 latency triage, provider outage runbook, cost-overrun response |
| `langchain-prod-checklist` | 30-item go-live checklist with concrete thresholds (timeouts, retries, budget caps) |
| `langchain-ci-integration` | GitHub Actions, `FakeListChatModel`, test gates, dry-run validators |
| `langchain-deploy-integration` | LangServe, Cloud Run, Vercel Python runtime, secret management |

### Pro (P15-P20)

| Skill | Description |
|-------|-------------|
| `langchain-performance-tuning` | Streaming modes, batch concurrency, semantic caching, RedisChatMessageHistory |
| `langchain-cost-tuning` | Real token accounting, model tiering, cache hit rates, per-tenant budget enforcement |
| `langchain-rate-limits` | `asyncio.Semaphore`, token-bucket, exponential backoff, provider-specific limits |
| `langchain-security-basics` | Prompt injection defenses, tool allowlisting, PII redaction, output validation |
| `langchain-enterprise-rbac` | Tenant isolation, per-tenant rate limits, role-scoped retrievers, audit logs |
| `langchain-multi-env-setup` | Pydantic `Settings` env validation, dev/staging/prod isolation, secret backends |

### Flagship (F21-F24)

| Skill | Description |
|-------|-------------|
| `langchain-reference-architecture` | Layered design, LLM factory, chain registry, DI, tenant-scoped vector stores |
| `langchain-webhooks-events` | Async callback handlers, SSE streaming, WebSocket, background event dispatch |
| `langchain-local-dev-loop` | `pytest`, `FakeListChatModel`, VCR fixtures, integration-test gating |
| `langchain-upgrade-migration` | 0.2 → 0.3 → 1.0 migration with named breaking changes, codemod hints |

### LangGraph v1.0 (L25-L34)

| Skill | Description |
|-------|-------------|
| `langchain-langgraph-basics` | `StateGraph`, typed state (TypedDict), nodes, edges, `compile()`, recursion limits |
| `langchain-langgraph-agents` | `create_react_agent`, prebuilt tool-calling agent, `tools_condition`, agent loop caps |
| `langchain-langgraph-checkpointing` | `MemorySaver`, `PostgresSaver`, `thread_id` semantics, time-travel, state history |
| `langchain-langgraph-human-in-loop` | `interrupt_before`, `interrupt_after`, `Command(resume=...)`, approval flows |
| `langchain-langgraph-streaming` | `stream_mode="messages"` vs `"updates"` vs `"values"`, token-level streaming |
| `langchain-langgraph-subgraphs` | Composing graphs, nested agent teams, shared state, subgraph boundaries |
| `langchain-middleware-patterns` | 1.0 middleware model, PII redaction, caching, retry middleware, ordering rules |
| `langchain-deep-agents` | Deep Agents pattern: planner + subagents + virtual filesystem + reflection loop |
| `langchain-otel-observability` | Native OTEL export, Jaeger/Honeycomb config, LLM-specific SLO dashboards |
| `langchain-content-blocks` | Typed `AIMessage.content` (text / tool_use / image), Claude tool_use iteration quirks |

## Quick Start

### 1. Install the pack

```bash
/plugin install langchain-py-pack@claude-code-plugins-plus
```

### 2. Install LangChain 1.0 + LangGraph 1.0 in your project

```bash
python -m venv .venv && source .venv/bin/activate

pip install "langchain>=1.0,<2.0" "langchain-core>=1.0,<2.0" \
            "langchain-anthropic>=1.0,<2.0" \
            "langgraph>=1.0,<2.0"
```

### 3. Write a minimal agent

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

### 4. Go to production

Follow `langchain-prod-checklist` for the 30-item go-live list, then
`langchain-otel-observability` to wire native OTEL export.

## Key LangChain 1.0 / LangGraph 1.0 Links

- [LangChain 1.0 release notes](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [LangChain Python docs](https://python.langchain.com/docs/) - primary reference
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph streaming modes](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- [`astream_events` v2](https://python.langchain.com/docs/how_to/streaming/#using-stream-events)
- [Checkpointing and persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Human-in-the-loop patterns](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [LangSmith](https://smith.langchain.com) - tracing and eval
- [State of Agent Engineering 2026](https://www.langchain.com/state-of-agent-engineering)

## Version Baseline

Every skill in this pack is `tested-against: langchain-core 1.0.x` / `langgraph 1.0.x`.
If you are on 0.2.x or 0.3.x, start with `langchain-upgrade-migration`.

## License

MIT
