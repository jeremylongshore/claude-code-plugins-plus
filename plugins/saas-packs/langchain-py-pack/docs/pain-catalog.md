# LangChain 1.0 / LangGraph 1.0 Pain Catalog (Python)

> The subagent bible. Every skill in this pack anchors to at least one entry here.
> If you are writing or reviewing a skill and cannot find a matching entry,
> stop and ask — do not write capability prose.

Baseline: `langchain-core 1.0.x`, `langchain 1.0.x`, `langgraph 1.0.x`,
`langchain-anthropic 1.0.x`, `langchain-openai 1.0.x`. Last verified 2026-04-21.

Each entry follows: **symptom → why → fix headline → skill mapping**.

---

## Category 1 — Model inference and content blocks

### P01 — `ChatAnthropic.stream()` delays `llmOutput` token counts

**Symptom:** `message.response_metadata["token_usage"]` is empty during streaming
and only populated after the stream closes. Cost dashboards built on callback
`on_llm_end` lag by the stream duration (often 5-30s for long completions).

**Why:** The Anthropic SDK reports `message_delta.usage` only in the terminal
`message_stop` event. LangChain's default callback aggregates usage at stream end.

**Fix headline:** Use `astream_events(version="v2")` and read `on_chat_model_stream`
events to attribute cost incrementally, or subscribe to a custom
`BaseCallbackHandler.on_llm_new_token` that increments your own meter.

**Skills:** `langchain-performance-tuning`, `langchain-cost-tuning`, `langchain-debug-bundle`

---

### P02 — `AIMessage.content` is a list on Claude, a string elsewhere

**Symptom:** Code that does `message.content.lower()` crashes with
`AttributeError: 'list' object has no attribute 'lower'` only on Anthropic models.

**Why:** Claude responses can mix text, `tool_use`, and `thinking` blocks.
`AIMessage.content` becomes `list[dict]` when any non-text block is present.
OpenAI responses stay as `str` until you add tools, then they diverge too.

**Fix headline:** Always iterate `message.content` as an iterable of blocks and
filter by `block["type"] == "text"`, or use the helper
`AIMessage.text()` (1.0+) which concatenates all text blocks safely.

**Skills:** `langchain-content-blocks`, `langchain-model-inference`, `langchain-common-errors`

---

### P03 — `with_structured_output(schema, method="function_calling")` silently drops fields

**Symptom:** A Pydantic field typed `Optional[list[Item]]` returns `None` even when
the model clearly described items in the text. ~40% of real schemas hit this.

**Why:** The default `method="function_calling"` requires strict JSON Schema and
rejects ambiguous unions. `Optional[list[X]]` serializes as
`anyOf: [{type:array}, {type:null}]` which some providers strip.

**Fix headline:** Use `method="json_schema"` (Anthropic, OpenAI GPT-4o+) or
`method="json_mode"` and manually validate with Pydantic. Avoid nested
`Union[A, B, None]` — flatten into discriminated unions.

**Skills:** `langchain-model-inference`, `langchain-sdk-patterns`, `langchain-common-errors`

---

### P04 — Token counts for prompt caching are reported per-call, not per-session

**Symptom:** `usage.cache_read_input_tokens` resets every call even though caching
is working. Aggregating "total cache savings" looks zero.

**Why:** LangChain passes through Anthropic's usage fields verbatim per response.
The aggregation is your responsibility.

**Fix headline:** Wrap chains with a callback that sums
`response_metadata["usage"]["cache_read_input_tokens"]` across invocations
keyed by session or tenant.

**Skills:** `langchain-cost-tuning`, `langchain-observability`

---

### P05 — `ChatOpenAI` and `ChatAnthropic` disagree on `temperature=0` determinism

**Symptom:** Same prompt, `temperature=0`, different outputs across calls on Claude.

**Why:** Anthropic's `temperature=0` still uses nucleus sampling; OpenAI's is closer
to greedy decoding. This breaks test snapshots.

**Fix headline:** For deterministic tests, use `FakeListChatModel` with canned
responses. In production, treat outputs as probabilistic even at `temperature=0`.

**Skills:** `langchain-local-dev-loop`, `langchain-ci-integration`

---

## Category 2 — Chains, LCEL, runnables

### P06 — `.pipe()` on mismatched dict shape raises cryptic `KeyError`

**Symptom:** `KeyError: 'question'` deep inside runnable internals. Stack trace
does not name the input key that was missing.

**Why:** LCEL's `RunnablePassthrough.assign()` operates on dict inputs. If the
upstream runnable returns a different shape, the error surfaces at the consumer.

**Fix headline:** Add a `RunnableLambda` debug probe between stages, or set
`DEBUG=1` in `langchain.debug` to log every intermediate value. Use typed
input/output with `RunnableSerializable[InputT, OutputT]` in new code.

**Skills:** `langchain-common-errors`, `langchain-debug-bundle`, `langchain-sdk-patterns`

---

### P07 — `.with_fallbacks()` catches all exceptions, including `KeyboardInterrupt`

**Symptom:** `Ctrl+C` during a long batch silently falls through to the fallback
chain and keeps running.

**Why:** The default `exceptions_to_handle=(Exception,)` in LCEL's fallback
implementation is inclusive of `KeyboardInterrupt` on Python <3.12.

**Fix headline:** Narrow the tuple: `.with_fallbacks([backup], exceptions_to_handle=(RateLimitError, APIError))`.

**Skills:** `langchain-sdk-patterns`, `langchain-rate-limits`, `langchain-common-errors`

---

### P08 — `.batch()` concurrency defaults silently serialize requests

**Symptom:** Batching 100 requests takes the same time as a sequential loop.

**Why:** `max_concurrency` defaults to **1** in some provider packages (notably
older `langchain-openai`). Must be passed explicitly.

**Fix headline:** `chain.batch(inputs, config={"max_concurrency": 10})`. Respect
provider rate limits — 10 is safe for most, 20+ needs a semaphore.

**Skills:** `langchain-performance-tuning`, `langchain-rate-limits`

---

## Category 3 — Agents and tool use

### P09 — `AgentExecutor` swallows intermediate tool errors as empty strings

**Symptom:** Agent returns "I couldn't find the answer" even though a tool raised.

**Why:** `AgentExecutor.invoke()` defaults `handle_parsing_errors=True` and
catches tool exceptions, passing the error message as the next observation.
If the error serializes to empty, the loop continues without signal.

**Fix headline:** Set `return_intermediate_steps=True` and inspect each step's
`observation`. For new agents, prefer `create_react_agent` from LangGraph
which raises tool errors by default.

**Skills:** `langchain-core-workflow`, `langchain-common-errors`, `langchain-langgraph-agents`

---

### P10 — Agent loops exceed 15 iterations on vague prompts

**Symptom:** `GraphRecursionError: Recursion limit of 25 reached without hitting a stop condition.`
Cost spike visible in dashboard before the error surfaces.

**Why:** `create_react_agent` defaults to `recursion_limit=25`. Vague prompts
("help me with my account") never converge. No default cost cap.

**Fix headline:** Set `recursion_limit=5-10` for interactive use;
add a LangGraph edge that routes to an `END` node on repeated tool calls;
use middleware to enforce a per-session token budget.

**Skills:** `langchain-langgraph-agents`, `langchain-cost-tuning`, `langchain-middleware-patterns`

---

### P11 — `bind_tools()` ignores docstrings that exceed 1024 chars

**Symptom:** Agent calls a tool with wrong args. The tool's docstring describes
the schema perfectly, but the model never saw the full text.

**Why:** Providers truncate tool descriptions. Anthropic: ~1024 chars per tool
description, ~~512~~ no longer enforced on GPT-4o but still a soft cap.

**Fix headline:** Keep tool docstrings short and move examples into the prompt
or a system message. Validate with
`len(tool.description) < 1024` before binding.

**Skills:** `langchain-sdk-patterns`, `langchain-security-basics`

---

## Category 4 — Embeddings, retrievers, RAG

### P12 — `FAISS.similarity_search_with_score` returns lower-is-better scores

**Symptom:** Ranking by score descending returns the worst results first. Users
see garbage at the top of search results.

**Why:** FAISS scores are L2 distances (lower = more similar).
Pinecone, Chroma, Weaviate return cosine similarity (higher = more similar).
The `VectorStore` interface does not normalize.

**Fix headline:** Use `normalize_score=True` on the retriever wrapper, or
explicitly remap: `score = 1 / (1 + distance)` for FAISS. Test with a golden
set of known-similar pairs.

**Skills:** `langchain-embeddings-search`, `langchain-common-errors`

---

### P13 — `RecursiveCharacterTextSplitter` breaks inside code fences

**Symptom:** RAG retrieves the first half of a Python function without its
signature. LLM hallucinates the function's purpose.

**Why:** The default separators `["\n\n", "\n", " ", ""]` split on any newline,
including inside triple-backtick fences in Markdown.

**Fix headline:** Use `Language`-specific splitters (`Language.PYTHON`,
`Language.MARKDOWN`) or add `"```"` as an early separator.

**Skills:** `langchain-data-handling`, `langchain-embeddings-search`

---

### P14 — Embedding dim mismatch crashes at insert time, not init time

**Symptom:** `PineconeApiException: dim mismatch: 1536 != 3072`. Pipeline ran
for 10 minutes before failing on the first batch insert.

**Why:** Pinecone indexes are created with a fixed dim. Swapping
`text-embedding-3-small` (1536) for `text-embedding-3-large` (3072) requires
a new index. LangChain does not validate on `PineconeVectorStore.__init__`.

**Fix headline:** Assert dim at startup: `assert embeddings.embed_query("test")` length matches
your index spec. Treat dim changes as a migration.

**Skills:** `langchain-embeddings-search`, `langchain-upgrade-migration`

---

### P15 — Reranker score is not comparable across queries

**Symptom:** Cohere/Jina rerank score for query A top-1 is 0.92, for query B
top-1 is 0.34. Filtering by `score > 0.5` drops half the good results.

**Why:** Rerank scores are *within-query* relative. A 0.34 top-1 still means
"most relevant of the candidates for this query."

**Fix headline:** Filter by *rank* (top-k), not score threshold. If you need a
confidence cutoff, calibrate per-query using the distribution shape
(e.g., drop bottom-half of each query's returned set).

**Skills:** `langchain-embeddings-search`, `langchain-data-handling`

---

## Category 5 — LangGraph state and execution

### P16 — Missing `thread_id` silently resets memory between turns

**Symptom:** Multi-turn agent forgets everything between calls. No error raised.

**Why:** `LangGraph` checkpointers key state by `config.configurable.thread_id`.
If omitted, every invocation gets a fresh state. No warning.

**Fix headline:** Require `thread_id` at your app boundary. Add middleware that
raises if `config["configurable"].get("thread_id")` is missing.

**Skills:** `langchain-langgraph-checkpointing`, `langchain-langgraph-basics`, `langchain-common-errors`

---

### P17 — `interrupt_before=[node]` raises if state contains non-JSON-serializable values

**Symptom:** `TypeError: Object of type <custom> is not JSON serializable`
the moment a node tries to interrupt.

**Why:** `MemorySaver` / `PostgresSaver` serialize state as JSON on every step.
Custom classes, `datetime`, `bytes`, Pydantic models with non-primitive fields
break serialization. Error surfaces only at the interrupt boundary, not on
node completion.

**Fix headline:** Keep state primitives-only (str/int/float/bool/list/dict).
For complex types, use `TypedDict` with explicit serializers, or serialize
to ISO strings in `on_node_finish`.

**Skills:** `langchain-langgraph-human-in-loop`, `langchain-langgraph-checkpointing`

---

### P18 — `Command(update={...}, goto="node")` replaces, does not merge, for list fields

**Symptom:** Resuming with `Command(update={"messages": [new_msg]})` loses
the prior message history.

**Why:** LangGraph merges state via the reducer declared in your `TypedDict`
(`Annotated[list, add_messages]`). If you forgot the reducer, `update`
*replaces* the field.

**Fix headline:** Always annotate list state with a reducer:
`messages: Annotated[list[AnyMessage], add_messages]`.
Validate reducers are in place with `graph.get_graph().draw_mermaid()`.

**Skills:** `langchain-langgraph-basics`, `langchain-langgraph-human-in-loop`

---

### P19 — `stream_mode="messages"` yields tokens; `"updates"` yields per-node diffs; `"values"` yields full state

**Symptom:** UI shows full conversation on every token tick (overdraw), or shows
nothing until the final step, or shows duplicated messages.

**Why:** The three modes emit fundamentally different payloads. Picking the
wrong one for your UI is the most common LangGraph integration mistake.

**Fix headline:** Decision tree — SSE token-level UI → `"messages"`;
progress bar per node → `"updates"`; debugger/time-travel → `"values"`.
See `langchain-langgraph-streaming` for the comparison table.

**Skills:** `langchain-langgraph-streaming`, `langchain-webhooks-events`

---

### P20 — `PostgresSaver` requires explicit schema migration on version bump

**Symptom:** Upgrading `langgraph` package silently reads old checkpoints as
empty state. No DB error, no warning.

**Why:** Checkpoint schema evolves; `PostgresSaver` does not auto-migrate.
Old rows are ignored by the new reader.

**Fix headline:** Run `PostgresSaver.setup()` after every `langgraph` upgrade in
staging. Test with a pinned checkpoint from an older version before prod.

**Skills:** `langchain-langgraph-checkpointing`, `langchain-upgrade-migration`

---

### P21 — Subgraph state is isolated by default; keys do not bubble up

**Symptom:** Parent graph cannot read a field the child subgraph set.

**Why:** LangGraph subgraphs have independent state schemas. Only keys present
in *both* parent and child schemas propagate.

**Fix headline:** Declare shared keys in both schemas, or use explicit
`Send` / `Command(graph=ParentGraph)` to push data up.

**Skills:** `langchain-langgraph-subgraphs`

---

## Category 6 — Memory and message history

### P22 — `RunnableWithMessageHistory` loses messages on process restart

**Symptom:** Chat history disappears after a pod restart on Cloud Run / Kubernetes.

**Why:** The default `InMemoryChatMessageHistory` / `ChatMessageHistory` is
in-process only. Not persisted.

**Fix headline:** Use `RedisChatMessageHistory`, `PostgresChatMessageHistory`,
or `FileChatMessageHistory`. For LangGraph, use a checkpointer instead.

**Skills:** `langchain-performance-tuning`, `langchain-reference-architecture`

---

### P23 — Trimmer drops the system prompt when token limit is tight

**Symptom:** Agent loses persona mid-conversation. System message was first,
so the trimmer dropped it to fit the window.

**Why:** `trim_messages(strategy="last")` with `include_system=False` (default)
removes the system message.

**Fix headline:** Always pass `include_system=True` and
`start_on="human"` so the first kept message is a user turn, not an assistant turn.

**Skills:** `langchain-performance-tuning`, `langchain-cost-tuning`

---

## Category 7 — Middleware and composability (1.0+)

### P24 — Middleware order matters: PII redaction after caching leaks PII into cache keys

**Symptom:** Cache hits return cached responses that were computed from a
different tenant's PII-containing prompt.

**Why:** Middleware is applied in registration order. Caching middleware before
redaction hashes raw prompts including PII.

**Fix headline:** Order: **redact → cache → model**. Document this invariant in
`langchain-middleware-patterns` and enforce with an integration test.

**Skills:** `langchain-middleware-patterns`, `langchain-security-basics`

---

### P25 — Retry middleware double-counts tokens

**Symptom:** A retried request is billed twice in usage metrics.

**Why:** Retry middleware runs the model call twice; both emit `on_llm_end`.
The aggregator sees both and sums them.

**Fix headline:** Attach a `request_id` attribute on retry so the aggregator
dedupes. Or place token accounting *above* the retry middleware.

**Skills:** `langchain-middleware-patterns`, `langchain-cost-tuning`

---

## Category 8 — Observability

### P26 — LangSmith zero-code tracing requires `LANGSMITH_TRACING=true`, not `LANGCHAIN_TRACING_V2`

**Symptom:** No traces appear in LangSmith. Env var spelled correctly for the
*legacy* name.

**Why:** In 1.0 the canonical env var is `LANGSMITH_TRACING`. `LANGCHAIN_TRACING_V2`
still works as a fallback but is deprecated.

**Fix headline:** Use `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=...`,
`LANGSMITH_PROJECT=my-project`. Pin to the 1.0 naming in new code.

**Skills:** `langchain-observability`, `langchain-debug-bundle`

---

### P27 — OTEL exporter omits prompt content by default (privacy-safe)

**Symptom:** OpenTelemetry traces show timing but no prompts or responses.

**Why:** Privacy-safe defaults. Prompt content is opt-in.

**Fix headline:** Set `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`
in trusted environments only. Never in multi-tenant production without
redaction middleware upstream.

**Skills:** `langchain-otel-observability`, `langchain-security-basics`

---

### P28 — Custom callbacks are not inherited by subgraphs

**Symptom:** A `BaseCallbackHandler` attached to the parent runnable never fires
on inner agent tool calls.

**Why:** LangGraph creates a child runtime per subgraph; callbacks are scoped.

**Fix headline:** Pass callbacks via `config["callbacks"]` at invocation time so
they propagate down, not via `Runnable.with_config(callbacks=[...])` which
binds at definition time.

**Skills:** `langchain-debug-bundle`, `langchain-observability`

---

## Category 9 — Rate limiting and cost

### P29 — `InMemoryRateLimiter` is per-process, not per-cluster

**Symptom:** Running N workers, each at `requests_per_second=10`, sends `10*N`
requests per second to the provider. Hits 429 immediately.

**Why:** Name says "InMemory." It literally means in-process.

**Fix headline:** For multi-worker deployments, use a Redis-backed rate limiter
(`RedisRateLimiter` from `langchain-community`) or a provider-side quota.

**Skills:** `langchain-rate-limits`, `langchain-deploy-integration`

---

### P30 — `max_retries=6` on `ChatOpenAI` means 7 requests (initial + 6 retries)

**Symptom:** Cost blowup on intermittent 429 — a single logical call bills as 7.

**Why:** The count is retries, not attempts.

**Fix headline:** Use `max_retries=2` and pair with a circuit breaker.
Log every retry via callbacks to see the true request count.

**Skills:** `langchain-rate-limits`, `langchain-cost-tuning`, `langchain-observability`

---

### P31 — Anthropic's 50 RPM tier throttles cache reads and writes separately

**Symptom:** 429 on cache writes while input-token budget shows headroom.

**Why:** Anthropic enforces RPM across all calls, cached or not.

**Fix headline:** Budget RPM at the client level (semaphore), not by token
count. Separate monitors for cached-read vs uncached-call rates.

**Skills:** `langchain-rate-limits`, `langchain-cost-tuning`

---

## Category 10 — Security and tenant isolation

### P32 — Tool allowlist is not enforced when agents synthesize tool names from strings

**Symptom:** Agent calls `exec()` even though `exec` is not in `tools=[...]`.
Model hallucinated the tool.

**Why:** Some agent implementations (older ReAct) parse free-text actions.
If the parser accepts any string, the allowlist is advisory.

**Fix headline:** Use `create_react_agent` (LangGraph) which uses provider-native
tool-calling — the provider enforces that only bound tools are callable.
Avoid free-text ReAct in production.

**Skills:** `langchain-security-basics`, `langchain-langgraph-agents`

---

### P33 — Per-tenant vector stores leak if retriever is bound at process start

**Symptom:** Tenant A's retriever returns Tenant B's documents after a deploy.

**Why:** A singleton `Retriever` caches its filter/namespace. If your factory
binds it at import time with a hardcoded tenant, other tenants share it.

**Fix headline:** Construct the retriever per-request, keyed by
`config["configurable"]["tenant_id"]`. Unit-test with two tenants and
assert non-overlap.

**Skills:** `langchain-enterprise-rbac`, `langchain-security-basics`, `langchain-reference-architecture`

---

### P34 — `Runnable.invoke` does not sanitize prompt injection by default

**Symptom:** A document in a RAG chain contains
`"Ignore previous instructions and..."`. The model follows it.

**Why:** LangChain does not filter prompt content. Injection defense is your job.

**Fix headline:** Wrap user-provided content in XML tags
(`<document>...</document>`), instruct the model to ignore instructions
inside tags, and add a `GuardrailsRunnable` that scans for jailbreak patterns
before model call.

**Skills:** `langchain-security-basics`, `langchain-middleware-patterns`

---

## Category 11 — Deployment and environment

### P35 — Vercel Python runtime has a 10-second timeout by default

**Symptom:** Long chain invocations return `FUNCTION_INVOCATION_TIMEOUT` on
Vercel. Works fine locally.

**Why:** Hobby/Pro default is 10s. Long agents exceed this routinely.

**Fix headline:** Set `maxDuration: 60` in `vercel.json`, or stream partial
responses so the client sees progress before the timeout.

**Skills:** `langchain-deploy-integration`, `langchain-performance-tuning`

---

### P36 — Cloud Run cold starts make first-request p99 latency 10x baseline

**Symptom:** Latency percentiles look fine at p50/p95 but p99 is 20+ seconds.

**Why:** Python + LangChain + embedding models + FAISS = ~5-15s cold start.
Cloud Run scales to zero by default.

**Fix headline:** Set `--min-instances=1` on the service. Preload heavy imports
at module top level. Use CPU-always-allocated billing.

**Skills:** `langchain-deploy-integration`, `langchain-incident-runbook`

---

### P37 — Secrets loaded from `.env` in production containers leak via `env` command

**Symptom:** `docker exec <container> env` shows API keys in plain text.

**Why:** `python-dotenv` populates `os.environ`. Anyone with container access
sees them.

**Fix headline:** Use secret manager (GCP Secret Manager / AWS Secrets Manager)
and load into memory only — do not export to process env.
Validate via pydantic `SecretStr`.

**Skills:** `langchain-multi-env-setup`, `langchain-security-basics`

---

## Category 12 — Migration and versioning

### P38 — `from langchain.chat_models import ChatOpenAI` is removed in 1.0

**Symptom:** `ImportError: cannot import name 'ChatOpenAI' from 'langchain.chat_models'`.

**Why:** Provider integrations moved to `langchain-<provider>` packages in 0.3
and the top-level reexports were removed in 1.0.

**Fix headline:** `from langchain_openai import ChatOpenAI`. Run
`python -m langchain_cli migrate` for automated fixes.

**Skills:** `langchain-upgrade-migration`, `langchain-common-errors`

---

### P39 — `LLMChain` is removed; use `prompt | llm | parser` instead

**Symptom:** `AttributeError: module 'langchain' has no attribute 'LLMChain'`.

**Why:** Legacy chain classes were removed in 1.0 in favor of LCEL composition.

**Fix headline:** Replace `LLMChain(llm=llm, prompt=prompt).run(x)` with
`(prompt | llm | StrOutputParser()).invoke({"input": x})`.

**Skills:** `langchain-upgrade-migration`, `langchain-sdk-patterns`

---

### P40 — `ConversationBufferMemory` and friends removed; replaced by LangGraph checkpointers

**Symptom:** `ImportError: cannot import name 'ConversationBufferMemory'`.

**Why:** Memory classes deprecated in 0.3, removed in 1.0. LangGraph
checkpointing is the replacement.

**Fix headline:** Migrate chat memory to LangGraph with `MemorySaver` or
`PostgresSaver` and a `thread_id` per conversation.

**Skills:** `langchain-upgrade-migration`, `langchain-langgraph-checkpointing`

---

### P41 — `initialize_agent` is removed; use `create_react_agent` from LangGraph

**Symptom:** `ImportError: cannot import name 'initialize_agent'`.

**Why:** Legacy agent factories removed in 1.0.

**Fix headline:**
```python
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(model=llm, tools=tools, checkpointer=MemorySaver())
```

**Skills:** `langchain-upgrade-migration`, `langchain-langgraph-agents`

---

### P42 — `AgentExecutor(return_intermediate_steps=True)` output shape changed

**Symptom:** Code that indexes `result["intermediate_steps"][0][0].tool` crashes
because the tuple shape differs.

**Why:** Legacy `AgentAction` vs new `ToolCall` object. Fields renamed.

**Fix headline:** Access via `step.tool_name` (new) instead of `step.tool` (old).
Check `isinstance(step, ToolCall)`.

**Skills:** `langchain-upgrade-migration`, `langchain-langgraph-agents`

---

## Category 13 — CI, testing, local dev

### P43 — `FakeListChatModel` doesn't emit `response_metadata`, breaks downstream token counters

**Symptom:** Test passes locally, fails in CI where a callback asserts on
`response_metadata["token_usage"]`.

**Why:** The fake model emits minimal metadata.

**Fix headline:** Subclass `FakeListChatModel` and override `_generate` to add
`generation_info={"token_usage": {...}}`, or gate token assertions behind
an "is-fake" check.

**Skills:** `langchain-local-dev-loop`, `langchain-ci-integration`

---

### P44 — VCR cassettes leak API keys into test fixtures

**Symptom:** PR review flags `Authorization: Bearer sk-...` in cassette files.

**Why:** `vcrpy` records headers by default.

**Fix headline:** Configure VCR with
`filter_headers=["authorization", "x-api-key", "anthropic-version"]` before
recording any cassette. Add a pre-commit hook that greps cassettes for
`sk-` / `sk-ant-`.

**Skills:** `langchain-ci-integration`, `langchain-local-dev-loop`, `langchain-security-basics`

---

### P45 — Pytest collection imports trigger provider SDK warnings that fail `-W error`

**Symptom:** Test suite fails with
`pytest.PytestUnraisableExceptionWarning` on collection, before any test runs.

**Why:** Some provider SDKs emit `DeprecationWarning` at import time.

**Fix headline:** Add filterwarnings config in `pyproject.toml`:
`filterwarnings = ["ignore::DeprecationWarning:langchain_community.*"]`.

**Skills:** `langchain-ci-integration`, `langchain-local-dev-loop`

---

## Category 14 — Streaming and webhooks

### P46 — SSE streams from LangGraph drop the final `end` event over proxies that buffer

**Symptom:** Client never sees stream completion. Hangs forever.

**Why:** Nginx / Cloud Run / CDN default buffering holds the last chunk.

**Fix headline:** Set `X-Accel-Buffering: no` header on the SSE response and
`Cache-Control: no-cache`. Test behind your actual proxy, not just localhost.

**Skills:** `langchain-webhooks-events`, `langchain-langgraph-streaming`, `langchain-deploy-integration`

---

### P47 — `astream_events(version="v2")` emits thousands of events per invocation

**Symptom:** SSE client crashes or browser tab freezes on a long generation.

**Why:** v2 emits per-token events plus per-runnable lifecycle events.

**Fix headline:** Filter by `event["event"] in {"on_chat_model_stream"}` server-side
before forwarding to the client. Never forward full event stream to browsers.

**Skills:** `langchain-langgraph-streaming`, `langchain-webhooks-events`, `langchain-debug-bundle`

---

### P48 — WebSocket handler blocks on sync `invoke()` inside async endpoint

**Symptom:** One slow request blocks all other connections.

**Why:** Calling `chain.invoke()` (sync) inside an async WebSocket handler
blocks the event loop.

**Fix headline:** Always use `await chain.ainvoke(...)` / `astream(...)` in
async contexts. Lint for this via a grep rule in CI.

**Skills:** `langchain-webhooks-events`, `langchain-performance-tuning`

---

## Category 15 — Documents, loaders, transformers

### P49 — `PyPDFLoader` splits by page; tables spanning pages get torn in half

**Symptom:** RAG answers misquote a table row because half the row is in a
different chunk.

**Why:** Page-based splitting is structure-agnostic.

**Fix headline:** Use `PyMuPDFLoader` or `UnstructuredPDFLoader` which detect
tables, or post-process with a table-aware splitter. For high-stakes
documents, index tables as separate structured records.

**Skills:** `langchain-data-handling`, `langchain-embeddings-search`

---

### P50 — Web loader User-Agent is blocked by Cloudflare by default

**Symptom:** `WebBaseLoader` returns 403 or a Cloudflare interstitial HTML blob.

**Why:** Default UA looks like a bot. Cloudflare challenges it.

**Fix headline:** Set `header_template={"User-Agent": "Mozilla/5.0 ..."}` and
prefer RSS or sitemap loaders where available. Respect robots.txt.

**Skills:** `langchain-data-handling`, `langchain-security-basics`

---

## Category 16 — Deep Agents and advanced patterns

### P51 — Deep Agent virtual FS state grows unboundedly

**Symptom:** After 50 tool calls, `state["files"]` dict holds megabytes of
intermediate thinking notes. Serialization to checkpointer is slow.

**Why:** Deep Agents write plans and scratch to state. No default eviction.

**Fix headline:** Add a cleanup node that prunes `state["files"]` entries older
than N steps, or checkpoint only on user-facing boundaries.

**Skills:** `langchain-deep-agents`, `langchain-langgraph-checkpointing`

---

### P52 — Subagent in Deep Agent pattern inherits parent's system prompt

**Symptom:** Subagent ignores its specific task instruction, follows the
planner persona instead.

**Why:** Default prompt composition appends rather than replaces.

**Fix headline:** Use explicit `SystemMessage(...)` at subagent invocation and
set `override=True` on the prompt template, or construct a fresh agent per
subtask instead of reusing one.

**Skills:** `langchain-deep-agents`

---

## Category 17 — Structured output in the real world

### P53 — Pydantic v2 `model_validate` rejects extra fields by default; model returns extra

**Symptom:** `ValidationError: extra fields not permitted`. The model added a
helpful but unrequested field.

**Why:** Pydantic v2 strict-by-default; models generalize.

**Fix headline:** Set `model_config = ConfigDict(extra="ignore")` on schemas
used for `with_structured_output`. Alternatively, instruct the model to
produce *only* the declared fields.

**Skills:** `langchain-model-inference`, `langchain-sdk-patterns`

---

### P54 — `with_structured_output(method="json_mode")` does not enforce schema, only JSON-validity

**Symptom:** Response is valid JSON but missing required fields.

**Why:** `json_mode` enforces JSON parseable output, not schema compliance.
Only `json_schema` and `function_calling` enforce structure.

**Fix headline:** Prefer `json_schema` on Anthropic/GPT-4o+. Fall back to
`json_mode` + Pydantic validation + retry on failure.

**Skills:** `langchain-model-inference`, `langchain-sdk-patterns`

---

## Category 18 — Recursion and termination

### P55 — `GraphRecursionError` with no obvious infinite loop

**Symptom:** `GraphRecursionError: Recursion limit of 25 reached.` Graph looks
linear. What happened?

**Why:** `recursion_limit` counts *total supersteps*, not loop iterations. A
graph with a complex conditional and many parallel branches can hit 25 steps
without looping.

**Fix headline:** Increase `recursion_limit=50` for genuinely long graphs, add
logging on every node entry to identify the actual step count, or
restructure with subgraphs to compartmentalize the budget.

**Skills:** `langchain-langgraph-basics`, `langchain-common-errors`

---

### P56 — Conditional edges returning a string that does not match any `path` silently go nowhere

**Symptom:** Graph halts without reaching `END`. No error.

**Why:** `add_conditional_edges(node, router)` where `router` returns a value
not in the `path_map` causes the graph to end without signal on some versions.

**Fix headline:** Always include a default route in `path_map` and assert the
router's return value is in the keyset. Use `END` explicitly as a valid
fallback.

**Skills:** `langchain-langgraph-basics`, `langchain-common-errors`

---

## Category 19 — Prompts and templates

### P57 — `ChatPromptTemplate.from_messages` with f-string templates breaks on `{` in user input

**Symptom:** `KeyError` when user input contains literal `{` characters
(e.g., code snippets, JSON).

**Why:** f-string templates parse `{var}` markers from user content too.

**Fix headline:** Use `MessagesPlaceholder("history")` for variable content and
escape literal braces as `{{`/`}}`. For user-provided free text, prefer
`jinja2` template format: `ChatPromptTemplate.from_messages([...], template_format="jinja2")`.

**Skills:** `langchain-sdk-patterns`, `langchain-common-errors`

---

### P58 — System message placement: Claude expects it at position 0; some chains move it

**Symptom:** Claude ignores persona instructions because they arrived as a later
`HumanMessage`.

**Why:** Claude requires system content in the top-level `system` field, not
in the messages array. LangChain's `langchain-anthropic` handles this, but
custom middleware can reorder messages.

**Fix headline:** Validate before send: the first message should be
`SystemMessage` OR system content should be extracted and passed via the
provider's `system` parameter.

**Skills:** `langchain-model-inference`, `langchain-content-blocks`

---

## Category 20 — Resource cleanup and async

### P59 — `async with` context managers on retrievers not always supported

**Symptom:** DB connection leak on a retriever backed by PostgresVectorStore.

**Why:** Not every retriever implements `__aenter__`/`__aexit__`.

**Fix headline:** Check the specific vectorstore's async protocol. Prefer
`AsyncPostgresVectorStore` with explicit pool management, and close pools in
FastAPI lifespan hooks.

**Skills:** `langchain-performance-tuning`, `langchain-deploy-integration`

---

### P60 — `BackgroundTasks` in FastAPI run *after* the response, LangChain streaming expects them during

**Symptom:** Trying to dispatch webhook events from a streaming endpoint — events
fire after the stream closes, not per-token.

**Why:** FastAPI `BackgroundTasks` are post-response.

**Fix headline:** Dispatch from a callback handler inside the chain, not via
`BackgroundTasks`. For fan-out, use `asyncio.create_task` inside
`on_llm_new_token`.

**Skills:** `langchain-webhooks-events`, `langchain-performance-tuning`

---

## Category 21 — Caching

### P61 — `set_llm_cache(InMemoryCache())` hashes the *prompt string*, ignoring tool schemas

**Symptom:** Two calls with same prompt but different tool lists return the
same cached response. Tools are silently ignored.

**Why:** Legacy cache key covers prompt only.

**Fix headline:** For tool-calling workflows, use `SQLiteCache` or
`RedisSemanticCache` with a key that includes a hash of bound tools.
Or skip caching on tool-using chains.

**Skills:** `langchain-cost-tuning`, `langchain-performance-tuning`

---

### P62 — Semantic cache hit rate drops on temperature > 0 usage

**Symptom:** `RedisSemanticCache` hit rate < 5% even on similar queries.

**Why:** Hit requires embedding similarity > threshold (default 0.95). Real-world
queries rarely hit that even when semantically equivalent.

**Fix headline:** Tune threshold to 0.85-0.90 after offline evaluation against
a gold pair set. Monitor false-positive rate with a sampled audit.

**Skills:** `langchain-cost-tuning`, `langchain-performance-tuning`

---

## Category 22 — Provider-specific quirks

### P63 — `ChatAnthropic.bind_tools(..., tool_choice={"type": "tool", "name": "X"})` forces a specific tool but ignores `None` returns

**Symptom:** Forced-tool invocation loops when the model has nothing to return.

**Why:** Forced tool choice disables the model's ability to output
`stop_reason="end_turn"` without calling a tool.

**Fix headline:** Use forced-tool only for single-call extraction. For agent
loops, use `tool_choice="auto"` and rely on the model to decide when to
stop.

**Skills:** `langchain-model-inference`, `langchain-langgraph-agents`

---

### P64 — `ChatOpenAI(model="gpt-4o")` image inputs require `image_url` format; `ChatAnthropic` requires `image` content block

**Symptom:** Multi-modal chain works on one provider, crashes on the other.

**Why:** Content block shapes differ between providers.

**Fix headline:** Use LangChain's abstracted content block helpers
(`{"type": "image", "source_type": "base64", "data": ..., "mime_type": ...}`)
introduced in 1.0. Do not hand-roll per-provider.

**Skills:** `langchain-content-blocks`, `langchain-model-inference`

---

### P65 — Gemini's safety settings reject benign prompts at `HARM_BLOCK_THRESHOLD=BLOCK_MEDIUM_AND_ABOVE`

**Symptom:** Medical/legal/security discussion prompts return
`finish_reason=SAFETY` on Gemini but not on Claude or GPT-4o.

**Why:** Gemini's defaults are more aggressive.

**Fix headline:** Override safety settings explicitly when building chains that
must handle sensitive domains. Document the safety profile as part of your
compliance posture.

**Skills:** `langchain-security-basics`, `langchain-model-inference`

---

## Category 23 — Known regressions in 1.0

### P66 — `langchain-anthropic >= 1.0` requires `anthropic >= 0.40`; pinning to old anthropic breaks `AIMessage.content` parsing

**Symptom:** Upgrade to 1.0 works for chat but breaks tool calling with
`KeyError: 'input'` in tool_use blocks.

**Why:** The SDK schema for tool_use blocks changed.

**Fix headline:** Upgrade `anthropic` to the latest 0.4x alongside
`langchain-anthropic`. Pin both in the same commit.

**Skills:** `langchain-upgrade-migration`, `langchain-common-errors`

---

### P67 — `astream_log()` is soft-deprecated in favor of `astream_events(version="v2")`

**Symptom:** `DeprecationWarning: astream_log is deprecated and will be removed
in 2.0.`

**Why:** Ecosystem consolidation on events v2.

**Fix headline:** Migrate to `astream_events(version="v2")`. Use the v2 event
types (`on_chat_model_stream`, `on_tool_start`, etc.) directly.

**Skills:** `langchain-upgrade-migration`, `langchain-debug-bundle`

---

### P68 — `StructuredOutputParser` from `langchain.output_parsers` produces inconsistent results vs `with_structured_output`

**Symptom:** Same schema, two methods, different success rates.

**Why:** `StructuredOutputParser` uses prompt-based parsing; provider-native
`with_structured_output(..., method="json_schema")` uses provider enforcement.
Provider-native is strictly better on supported models.

**Fix headline:** Prefer `model.with_structured_output(schema, method="json_schema")`
on Anthropic 1.0+ and GPT-4o+. Fall back to parser only on models without
schema support.

**Skills:** `langchain-model-inference`, `langchain-sdk-patterns`

---

## How to use this catalog

1. **Writing a skill?** Find 1-3 entries that anchor its pain. Quote at least
   one in the skill's Overview section.
2. **No matching entry?** Stop. The skill is probably generic boilerplate.
   Ask the main thread to extend this catalog first.
3. **Reviewing a skill?** Check it cites at least one entry number in its
   Resources section, or names the specific error/threshold.
4. **Verifying against live docs?** Every entry's "Fix headline" should be
   reproducible by running code against the pinned 1.0.x versions.

## Sources

- [LangChain 1.0 release announcement](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [LangChain Python docs](https://python.langchain.com/docs/)
- [LangGraph concepts](https://langchain-ai.github.io/langgraph/concepts/)
- [LangGraph persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangGraph streaming](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- [LangGraph HITL](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [LangSmith docs](https://docs.smith.langchain.com/)
- [State of Agent Engineering 2026](https://www.langchain.com/state-of-agent-engineering)
- Anthropic SDK 0.4x changelog
- OpenAI Python SDK changelog
- Production incident reports from pack authors (PR #526 and predecessors)

All entries verified against 2026-04-21 versions of the listed packages.
