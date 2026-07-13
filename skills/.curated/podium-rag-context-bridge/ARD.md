# ARD: Podium RAG Context Bridge

## Architecture Pattern

**Library + scripts.** The core is a small async retrieval substrate (`build_context`) plus a vector-store adapter (`PgvectorStore`) plus pluggable embedder + reranker `Protocol` interfaces plus a redaction filter plus a token-budget enforcer. The library is async-first because all four surfaces (embed, vector query, rerank, live Podium fetch) are I/O-bound and the deadline is non-negotiable. Operator CLIs (`context_fetch.py`, `vector_query.py`, `transcript_to_llm.py`, `relevance_score.py`) wrap the library for one-shot use and integration testing.

Pattern: **Parallel fan-out under a hard deadline, with asymmetric merge (live wins), defense-in-depth redaction, and rerank-priority token-budget eviction.**

## Workflow

```
                ┌──────────────────────────────────┐
                │ transcript_chunk + contact_uid   │
                └──────────────┬───────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ TranscriptCoalescer.feed(chunk)  │
                │  prepend tail of previous chunk  │
                └──────────────┬───────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ embedder.embed(coalesced_query)  │
                └──────────────┬───────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │ asyncio.gather (parallel)       │
              │                                 │
              ▼                                 ▼
   ┌────────────────────────┐       ┌──────────────────────────┐
   │ vector_store.query     │       │ fetch_live_contact       │
   │  pool_k=20, filter:    │       │  GET /v4/contacts/{uid}  │
   │  contact_uid           │       │  via podium-auth         │
   └──────────┬─────────────┘       └────────────┬─────────────┘
              │                                  │
              ▼                                  │
   ┌────────────────────────┐                    │
   │ reranker.score(query,  │                    │
   │  candidates)           │                    │
   │  rerank to final_k=5   │                    │
   └──────────┬─────────────┘                    │
              │                                  │
              └──────────────────┬───────────────┘
                                 │
                                 ▼
                ┌──────────────────────────────────┐
                │ merge_live_over_vector(...)      │
                │  live wins on LIVE_FIELDS        │
                └──────────────┬───────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ redact_bundle(...)               │
                │  CC / SSN / email / phone / DOB  │
                └──────────────┬───────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ enforce_budget(max_tokens=1500)  │
                │  drop lowest-rerank first        │
                └──────────────┬───────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ attach meta.{elapsed_ms,         │
                │   partial, had_vector_hits,      │
                │   had_live_lookup}               │
                └──────────────┬───────────────────┘
                               │
                               ▼
                       JSON bundle to caller

   ─── hard deadline (default 800ms) bounds the whole pipeline ───
   any surface that misses the deadline yields its slot to the
   merge step with meta.partial=true; bundle still emits
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. Opens with the six production failures the substrate prevents so a reader recognizes the problem space before reading any code. Then one mitigation per failure mode in execution order.
- **PRD.md** is the product framing — three personas (Priya/Ravi/Mark), acceptance criteria, success metrics, risk register. The "AI engineer + integration engineer + business owner" triple maps to who lives with the bridge's output.
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together and why each interface exists.
- **references/errors.md** is a flat lookup table — `ERR_RAG_*` → cause + solution — for incident response.
- **references/examples.md** is a cookbook of full worked snippets (single-tenant, agent-loop, sandbox eval, fault drills).
- **references/implementation.md** is the language-portability + vector-store-portability layer: pgvector schema, Pinecone/Weaviate adapters, embedder + reranker swaps, the ingest hook for `podium-conversation-history-export`.
- **scripts/** are executable operator tools; each is single-responsibility and prints structured output (JSON-on-stdout, human-on-stderr) so they compose.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read             # read config, secret-store files, source for sanity audits
  - Write            # write redacted-bundle samples, eval datasets, schema migrations
  - Edit             # edit redaction patterns, prompt templates, ingest hooks
  - Bash(curl:*)     # call live Podium API in shell examples
  - Bash(jq:*)       # parse JSON responses in shell examples
  - Bash(python3:*)  # invoke the operator scripts
  - Bash(psql:*)     # apply the pgvector schema, inspect retrievals
  - Grep             # audit emitted bundles for PII regex matches, smoke-test redaction
```

`Bash(rm:*)` and `Bash(git:*)` are intentionally absent — this skill never deletes files and never makes git commits. PII audit findings are reported; the operator decides remediation.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-rag-context-bridge/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml            # pool/final K, timeouts, redaction patterns, embedder + reranker defaults
├── references/
│   ├── errors.md                # ERR_RAG_001..014 with cause + solution
│   ├── examples.md              # 10 worked examples
│   └── implementation.md        # pgvector schema, store adapters, model swaps, ingest hook
└── scripts/
    ├── context_fetch.py         # CLI: transcript chunk + contact → JSON bundle
    ├── vector_query.py          # CLI: raw two-stage retrieval with rerank
    ├── transcript_to_llm.py     # CLI: format a turn + bundle into an LLM prompt
    └── relevance_score.py       # CLI: score (query, candidate) ∈ [0, 1]
```

## API Integration Architecture

Four upstream surfaces; one method each:

| Surface | Method | Wrapping |
|---|---|---|
| Embedding model | `embedder.embed(text)` | Pluggable via `Embedder` Protocol; default `BAAI/bge-large-en-v1.5` (sentence-transformers) |
| Vector store | `vector_store.query(emb, top_k, filter)` | Pluggable via `VectorStore` Protocol; default pgvector reference impl |
| Cross-encoder reranker | `reranker.score(query, candidates)` | Pluggable via `Reranker` Protocol; default `BAAI/bge-reranker-base`; no-op reranker available |
| Podium live contact | `fetch_live_contact(auth, uid)` | Uses `podium-auth` for token; only field is `GET /v4/contacts/{uid}` |

All four are called concurrently inside the deadline. A timeout on any one surface yields its slot to the merge step with `meta.partial=true` recorded; the bundle still emits.

## Data Flow Architecture

```
[Ingest, separate pipeline]               [Live Podium]                 [Vector Store]
       │                                       │                              │
  (export skill emits)                         │                              │
  conversation chunks                          │                              │
       │ embed + insert                        │                              │
       ├──────────────────────────────────────────────────────────────────────►
       │                                       │                              │
                  ── ── ── ── (separate from real-time path) ── ── ── ──
                                               │
                                               │       transcript chunk arrives
                                               │              │
                                               │              ▼
                                               │      [Coalescer + Embedder]
                                               │              │
                                               │     ┌────────┴────────┐
                                               │     │                 │
                                               │     ▼                 ▼
                                               │ vector query     live lookup
                                               │     │                 │
                                               │     ▼                 │
                                               │  rerank               │
                                               │     │                 │
                                               │     └────────┬────────┘
                                               │              ▼
                                               │           merge
                                               │              │
                                               │              ▼
                                               │           redact
                                               │              │
                                               │              ▼
                                               │         budget cap
                                               │              │
                                               │              ▼
                                               │           bundle ──► LLM
```

The ingest pipeline runs on its own SLA (offline, batch, idempotent). The retrieval pipeline runs on the call-duration SLA (real-time, sub-second, eventually-consistent with ingest). The bridge does not own ingest — it consumes the table the ingest pipeline writes.

## Error Handling Strategy

Three error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `RAGBudgetExceededError` | Total elapsed > timeout AND no surface completed | Return empty bundle with `meta.partial=true`; LLM grounds on transcript alone |
| `RAGRetrievalError` (transient) | Vector store 5xx, embedder timeout, reranker timeout | Skip the affected surface; emit partial bundle with `meta.had_vector_hits=false` |
| `RAGRedactionWarning` | Redactor matched a pattern in retrieved text | Log structured event; bundle still emits (the redaction succeeded — the warning is for ingest-pipeline followup) |

Retry policy is **caller-side**, not bridge-side — the bridge ships in real time; it has no retry budget. If the calling agent loop wants a second attempt, it issues a second `build_context` call on the next transcript chunk.

## Composability & Stacking

`podium-rag-context-bridge` is the **keystone skill** of the Podium agentic stack. Every other skill in the pack contributes input or consumes output:

```
                  ┌────────────────────────────────────────┐
                  │  podium-rag-context-bridge  ◄── this   │
                  │  (the substrate)                       │
                  └──────────────┬─────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │ consumes (input)   │   consumes (input) │ depends on
            ▼                    ▼                    ▼
  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
  │ podium-call-       │ │ podium-conversation│ │ podium-rate-limit- │
  │ transcript-        │ │ -history-export    │ │ survival           │
  │ pipeline           │ │ (corpus for vector │ │ (Podium-side       │
  │ (live chunks)      │ │  store, ingested   │ │  backoff)          │
  │                    │ │  separately)       │ │                    │
  └────────┬───────────┘ └─────────┬──────────┘ └─────────┬──────────┘
           │                       │                      │
           └───────────────────────┼──────────────────────┘
                                   │ all three rest on
                                   ▼
                         ┌──────────────────────┐
                         │  podium-auth         │
                         │  (OAuth foundation)  │
                         └──────────────────────┘
```

This is the keystone because the bridge is the only skill in the pack that produces the artifact the LLM directly consumes. Everything to the left of it is plumbing (auth, rate limits, transcript pipeline); everything to the right is the agent loop the customer paid for. If the bridge is wrong, every downstream model call is wrong.

A consumer of `podium-rag-context-bridge` gets, for free: cross-encoder reranking, asymmetric live-vs-vector merge, retrieval-time PII redaction, token-budget enforcement, hard-deadline degraded-mode signaling. None of these are re-implementable as a one-off — the discipline only works if it lives at the substrate.

## Performance & Scalability

- **Single-bridge throughput**: bounded by the slowest of (embedder, vector store, reranker, Podium live lookup) per call. With local `bge-large-en-v1.5` on a CPU, embed p99 is ~80ms; pgvector p99 over 100k rows is ~50ms; cross-encoder rerank p99 over 20 candidates is ~200ms; Podium p99 is ~300ms. Parallel fan-out collapses to ~max(rerank, podium) ≈ 300ms p95, ~500ms p99.
- **Multi-conversation concurrency**: linear in number of simultaneous calls; the bridge is stateless except for the coalescer (per-conversation). 100 concurrent calls on one process is trivial; horizontally scale beyond that.
- **Cold start**: embedder + reranker model load is ~3 seconds on CPU, ~1 second on GPU. Warm the models at process start; never on the first call.
- **Corpus growth**: pgvector with HNSW indexes stays under 100ms p99 to ~10M rows. Beyond that, sharding or Pinecone is appropriate.

## Security & Compliance

- **Vector-store credentials**: pgvector DSN held in the secret store (SOPS / AWS Secrets Manager / GCP Secret Manager — same posture as `podium-auth`). Plaintext never lands on disk.
- **Embedder / reranker keys**: if using hosted models (OpenAI), API keys held in the secret store. Local models have no keys.
- **Podium live lookup**: delegated to `podium-auth`; this skill never holds OAuth state itself.
- **PII**: retrieval-time regex redaction as defense-in-depth. The ingest pipeline (`podium-conversation-history-export`) is the primary redactor; the bridge is the last line of defense before emission. Audit logs flag every redaction-trigger so ingest can be improved.
- **Bundle emission logs**: log `meta` fields only, not the bundle content. The bundle contains customer PII even after redaction (e.g., the live phone number); it never lands in a centralized log.
- **Cross-contact leakage**: per-contact filter at the WHERE level in the vector query. Without `contact_uid`, the bridge returns unfiltered results — the calling agent is responsible for asserting it has identified the contact before searching unfiltered.

## Testing Strategy

- **Unit tests**: mock each of the four surfaces; verify the deadline is hard, the merge is asymmetric, redaction patterns match, budget eviction is rerank-priority.
- **Sandbox eval set**: 100 human-labeled (transcript_chunk, contact_uid, expected top-1 historical excerpt) triples; track top-1 precision against the labels; CI fails if precision drops below 0.80.
- **Fault drills**: chaos-test each surface — vector store returns empty, reranker times out, Podium returns 429, all surfaces timeout simultaneously. Verify the bundle still emits in every case.
- **Redaction smoke**: corpus of synthetic conversations with planted PII; verify zero PII reaches the emitted bundle.
- **Latency soak**: 7-day continuous run at 10 RPS against a real-shape corpus; verify p95 ≤ 800ms and `meta.partial` rate ≤ 5%.
- **Budget audit**: replay 1000 production calls; verify zero bundles exceed `max_tokens` for the historical-excerpts surface.

## Configuration Surface

All tunables in `config/settings.yaml`. The hot ones for operators:

| Knob | Default | What it controls |
|---|---|---|
| `retrieval.pool_k` | 20 | Pool size from the vector store before rerank |
| `retrieval.final_k` | 5 | Excerpts kept after rerank |
| `retrieval.timeout_ms` | 800 | Hard wall-clock deadline for `build_context` |
| `embedder.backend` | `bge-large-en-v1.5` | One of: bge-large-en-v1.5, openai-text-embedding-3-small |
| `reranker.backend` | `bge-reranker-base` | One of: bge-reranker-base, llm-reranker, none |
| `redaction.enabled` | `true` | Defense-in-depth PII filter |
| `budget.max_tokens_historical` | 1500 | Token cap on `historical_excerpts` surface |
| `coalescer.tail_window_ms` | 200 | Sliding-window overlap from prior chunk |
| `degraded.partial_alert_threshold` | 0.05 | Sustained `partial` rate that triggers a page |
