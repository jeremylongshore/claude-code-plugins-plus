# Errors — podium-rag-context-bridge

Lookup table for `ERR_RAG_*` codes raised by the library and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_RAG_001 — vector_store_unreachable

- **Surface**: vector store
- **Cause**: pgvector DSN refused connection, network partition, or store-side outage.
- **Detection**: `vector_store.query()` raises a connection error inside `with_deadline`.
- **Action**: Bundle emits with `meta.had_vector_hits=false` and live-only context. If sustained >5 minutes, page on-call — the bridge is operating in degraded mode and the LLM is missing historical grounding. Verify the secret-store DSN, check pgvector container health, then warm the connection pool.

## ERR_RAG_002 — embedder_timeout

- **Surface**: embedder
- **Cause**: Embedding model took longer than `retrieval.embed_budget_ms` AND longer than the remaining wall-clock budget.
- **Detection**: `embedder.embed()` raises `asyncio.TimeoutError` inside `with_deadline`.
- **Action**: Skip the vector surface entirely for this call (no embedding → no query). Live-only bundle emits. If sustained, swap to a smaller embedding model or move from CPU to GPU. Verify the model warmup ran at process start (cold-start embeds can take 3+ seconds).

## ERR_RAG_003 — reranker_timeout

- **Surface**: reranker
- **Cause**: Cross-encoder rerank exceeded `retrieval.rerank_budget_ms`.
- **Detection**: `reranker.score()` raises `asyncio.TimeoutError`.
- **Action**: Fall back to raw cosine score for ordering. Bundle emits with `historical_excerpts` ranked by ANN recall only (degraded relevance). If sustained, reduce `pool_k`, switch to `bge-reranker-base` from `-large`, or set `reranker.backend: none` to disable reranking entirely.

## ERR_RAG_004 — live_lookup_401

- **HTTP**: 401 from `GET /v4/contacts/{uid}`
- **Cause**: Podium access token rejected. Usually means `podium-auth` is in `ERR_AUTH_003` / `invalid_token` state.
- **Detection**: live-lookup task returns `{"error": 401}`.
- **Action**: Surface to `podium-auth` immediately — its token cache needs to refresh or it has hit `ERR_AUTH_001`. Bundle emits with `contact.live_fields_available=false`; vector-only context this call. Repeated 401s indicate the auth layer is broken, not this skill.

## ERR_RAG_005 — live_lookup_404

- **HTTP**: 404 from `GET /v4/contacts/{uid}`
- **Cause**: The `contact_uid` does not exist in this Podium org. Usually a routing bug (wrong org), a stale uid from the vector store, or the contact was deleted.
- **Detection**: live-lookup task returns `{"error": 404}`.
- **Action**: Bundle emits with `contact: {"error": 404}`. The vector store is queried WITHOUT the contact-uid filter so the LLM still gets some context (the calling agent must decide whether to ground on cross-contact retrieval). Log the bad uid for the operator to investigate.

## ERR_RAG_006 — live_lookup_429

- **HTTP**: 429 from `GET /v4/contacts/{uid}`
- **Cause**: Podium-side rate limit. Usually means the agent is making too many live lookups per second — possibly because the bridge is being called for every transcript chunk instead of every conversation turn.
- **Detection**: live-lookup task returns `{"error": 429}`.
- **Action**: Defer to `podium-rate-limit-survival` for backoff orchestration. Bundle emits vector-only; flag in `meta`. If sustained, audit the calling agent for over-fetching (one lookup per turn, not per chunk).

## ERR_RAG_007 — deadline_exceeded_full

- **Surface**: all
- **Cause**: Total elapsed exceeded `retrieval.timeout_ms` AND no surface completed.
- **Detection**: Both `vec_task` and `live_task` return `None` from `with_deadline`.
- **Action**: Empty bundle emits with `meta.partial=true`, `meta.had_vector_hits=false`, `meta.had_live_lookup=false`. The LLM grounds on transcript alone. If sustained >1% of calls, the bridge cannot meet its SLA on the current deployment — profile per-surface and scale the slowest.

## ERR_RAG_008 — redaction_pattern_match

- **Surface**: redactor
- **Cause**: Retrieval-time PII filter matched a pattern in retrieved text — the ingest pipeline missed redaction.
- **Detection**: `redact_bundle()` substituted a `[REDACTED:*]` marker.
- **Action**: Not a hard error — the redactor did its job. BUT this is a defense-in-depth event: log the matched pattern (NOT the matched value), the source row's `id`, and the ingest version that wrote it. Open a ticket against `podium-conversation-history-export` to fix ingest. Repeated matches against the same row indicate the ingest pipeline is regressing.

## ERR_RAG_009 — token_budget_drop

- **Surface**: budget enforcer
- **Cause**: Retrieved excerpts exceeded `budget.max_tokens_historical`; lowest-rerank excerpts were dropped.
- **Detection**: `enforce_budget()` returned with `meta.dropped_excerpts_count > 0`.
- **Action**: Informational. If sustained `dropped_excerpts_count > 0` across most calls, raise the budget (if the model window allows) or reduce `final_k`. The drop order is rerank-priority by design — high-relevance content is preserved.

## ERR_RAG_010 — token_budget_hard_truncate

- **Surface**: budget enforcer
- **Cause**: A single excerpt alone exceeded `max_tokens_historical`; it was hard-truncated with `truncated: true`.
- **Detection**: `enforce_budget()` set `e.truncated=true` on the single remaining excerpt.
- **Action**: The vector store has a chunk that is too large for the budget. Audit ingest chunking — chunks should be ≤ `max_tokens_historical / 2` so two can fit. Until ingest is fixed, the LLM sees a truncated excerpt with explicit `truncated: true` so it knows.

## ERR_RAG_011 — vector_dimension_mismatch

- **Surface**: vector store
- **Cause**: Embedder's output dimension does not match the vector store schema column type (e.g., embedder swap to `text-embedding-3-small` (1536) against a `vector(1024)` column).
- **Detection**: `psycopg` raises a `DataError` about vector dimensions.
- **Action**: This is a deployment misconfiguration, not a runtime issue. Either re-embed the corpus into a new table at the new dimension, OR roll back the embedder. Do not silently truncate or pad — that yields nonsense retrievals.

## ERR_RAG_012 — coalescer_state_too_large

- **Surface**: coalescer
- **Cause**: The per-conversation coalescer buffer grew unbounded — usually because `conversation_uid` was not provided and the bridge created a single global buffer that everything is sharing.
- **Detection**: Memory growth correlated with call volume; bundle quality degrades because cross-conversation tails are leaking into embed queries.
- **Action**: Plumb `conversation_uid` through the API. The coalescer is supposed to be keyed per-conversation. Disable the coalescer entirely (`coalescer.enabled: false`) if the calling agent already pre-processes chunks.

## ERR_RAG_013 — sustained_partial_rate

- **Surface**: degraded-mode monitor
- **Cause**: `meta.partial=true` rate over `degraded.rolling_window_seconds` exceeded `degraded.partial_alert_threshold` (default 5%).
- **Detection**: Background monitor or rolling p99 dashboard.
- **Action**: Page on-call. The bridge is in sustained degraded mode — at least one surface is not meeting its budget. Inspect per-surface p99 to identify the slow path (usually vector store or reranker). Scale or swap accordingly.

## ERR_RAG_014 — credential_leak_detected

- **Surface**: pre-commit / static audit
- **Cause**: A grep audit found a string matching an embedding-model API key, vector-store DSN, or Podium credential in tracked source.
- **Detection**: `grep -rnE` against the canonical leak regex (see `SKILL.md` pre-flight) returns non-empty.
- **Action**: Treat as a security incident. Rotate the leaked credential immediately. Verify `.gitignore` covers the secret-store path. Audit `git log -p` for the leak window and assess data-access scope. The bridge ships with placeholder tokens (`{your-pgvector-dsn}`, `{your-openai-key}`) precisely so this never triggers on the skill's own source.
