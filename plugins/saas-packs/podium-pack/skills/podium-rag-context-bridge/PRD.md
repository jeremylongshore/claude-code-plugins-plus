# PRD: Podium RAG Context Bridge

## Summary

**One-liner**: Real-time retrieval substrate that turns a Podium transcript chunk into a structured LLM-ready RAG context bundle — combining vector search over embedded conversation history with live Podium contact lookup, under a hard 800ms latency budget, with reranking, PII redaction, token-budget enforcement, and degraded-mode signaling.

**Domain**: Real-time AI agents / retrieval-augmented generation / SMB customer-engagement platforms

**Users**: AI engineers wiring transcription-driven agent loops, integration engineers connecting Podium to an LLM, small-business operators whose agents need cross-channel memory to be useful

## Problem Statement

The Podium platform ships call transcription and webchat events as a continuous stream. An LLM connected to that stream is only as good as the context it grounds on — and a naive RAG implementation is six different ways broken before it reaches a production call.

Top-K cosine similarity over an unfiltered corpus surfaces five chunks of "thanks for reaching out" boilerplate. The contact's phone number in the vector store is yesterday's value. The transcriber chunks across word boundaries so the order number never makes it into the embed query. The retrieved context plus system prompt overflows the model window and silently truncates. Credit-card-like strings the ingest pipeline forgot to redact reach the LLM intact. And by the time the bridge has finished all of the above serially, the customer hung up.

Off-the-shelf RAG libraries do not address any of these failure modes — they are scoped to "search a wiki and stuff results into a prompt," not to "real-time agentic grounding under a sub-second deadline with live state drift." This skill is the production-engineering layer Mark Kofahl described when he said the transcription needs to query an LLM that contains data from Google Workspace, Shopify, and Podium. The bridge is the half of that sentence that turns "transcription" into "queryable, current, redacted, budget-bounded context."

## Target Users

### Persona 1: AI Engineer (Priya)

- **Role**: Builds the agent loop. Owns the LLM-facing prompt template and the retrieval substrate that feeds it. Reports to a head of AI; deliverable is "agent-assisted call handling that beats the unassisted baseline on first-call-resolution."
- **Goals**: A retrieval surface she can call from her agent loop with a one-line API and trust to return inside her latency budget; clear separation between "live state" and "historical context" so she can reason about what the model is grounding on; deterministic behavior under degraded conditions (vector store slow → graceful fallback, not a hung loop).
- **Pain Points**: The first prototype was top-K=5 over a flat corpus, the model kept hallucinating order numbers, and her director asked "why is the model worse than no context?" She does not want to build the retrieval stack from scratch but also does not trust off-the-shelf RAG libraries to handle real-time correctness.
- **Technical Level**: High (LLM-fluent, comfortable with async Python, has shipped agentic systems before).

### Persona 2: Integration Engineer (Ravi)

- **Role**: Wires the Podium transcription stream into the agent loop and operates the bridge as a service. Owns the deployment, the observability, and the on-call playbook.
- **Goals**: A bridge that emits structured logs he can dashboard (p50/p95/p99 per surface), a clear failure model (which surfaces degraded, in what order), and an obvious answer for "the LLM said something wrong — what did the bridge ship to it?"
- **Pain Points**: The vector store went read-only for 40 minutes during a Podium webhook burst and the bridge silently fell back to live-only — nobody noticed until a CSM asked why the agent stopped referencing prior conversations. The bridge needed a `partial: true` flag that propagates to the model and the logs.
- **Technical Level**: High (production-ops-engineer; reads code, writes Terraform, lives in dashboards).

### Persona 3: Small-Business Owner (Mark archetype)

- **Role**: Owns a campervan retailer. Uses Podium across SMS, calls, and webchat. Asked for the LLM-driven agent because his team cannot scale call handling. Does not write code; pays a consultant to wire it.
- **Goals**: The agent says correct things about his customers. Stops asking returning customers their name. References the right order number. Does not call a number that's been disconnected for a year.
- **Pain Points**: His last attempt at an "AI for Podium" missed obvious context that was in the contact's webchat from last month — said it didn't know who the caller was when the caller had been a customer for 3 years. He fired the consultant; the system was not the problem, the retrieval was.
- **Technical Level**: Low (operator; outcomes-focused; does not care about the implementation, cares deeply about whether it works on the customer he is about to call).

## User Stories

### US-1: Transcript-chunk to context bundle (P0)

**As** an AI engineer,
**I want** to pass a transcript chunk + contact_uid and receive a structured JSON bundle in ≤800ms,
**So that** my agent loop can build an LLM prompt without blocking the call.

**Acceptance Criteria:**

- API surface: `build_context(transcript_chunk, contact_uid, ...) -> dict`
- p95 latency ≤ 800ms; p99 ≤ 1200ms on a 100k-chunk corpus
- Bundle shape includes `contact`, `historical_excerpts`, `token_count`, `meta`
- Returns even on full timeout (with `meta.partial: true`)

### US-2: Cross-encoder reranking (P0)

**As** an AI engineer,
**I want** retrieved excerpts reranked by a cross-encoder before they reach the model,
**So that** the top-5 the model sees are actually the top-5, not five copies of "thanks for reaching out."

**Acceptance Criteria:**

- Pool size `pool_k` configurable (default 20)
- Final size `final_k` configurable (default 5)
- Each excerpt carries both `cosine_score` (recall) and `rerank_score` (relevance)
- Reranker is pluggable: cross-encoder default, LLM-as-reranker optional

### US-3: Live state wins over vector state (P0)

**As** an AI engineer,
**I want** the contact's live fields (phone, opt_out, location) to override any stale vector embeddings,
**So that** the LLM never grounds on a number that hasn't worked in 16 hours.

**Acceptance Criteria:**

- Live Podium `GET /v4/contacts/{uid}` is called in parallel with vector search
- A documented `LIVE_FIELDS` set identifies which fields are always live
- Merge is asymmetric: live wins on `LIVE_FIELDS`, vector contributes content only

### US-4: PII redaction at retrieval time (P0)

**As** an integration engineer,
**I want** a redaction filter applied to retrieved excerpts before they reach the LLM,
**So that** even if ingest forgot to redact, the model never sees raw PII.

**Acceptance Criteria:**

- Patterns for CC, SSN, email, phone, DOB, street address applied
- Redaction is at retrieval time, AFTER merge, BEFORE emission
- Tokens replaced with `[REDACTED:KIND]` markers so the model can refer to them by category

### US-5: Token-budget enforcement (P1)

**As** an AI engineer,
**I want** the retrieved-excerpts surface bounded to a configurable token budget,
**So that** the LLM prompt never silently truncates from the middle.

**Acceptance Criteria:**

- Default budget: 1500 tokens for `historical_excerpts`
- Over-budget excerpts dropped lowest-rerank first
- Last excerpt hard-truncated only if it alone exceeds the budget, with `truncated: true` flag

### US-6: Hard deadline + degraded-mode signaling (P0)

**As** an integration engineer,
**I want** a hard wall-clock timeout that returns whatever surfaces completed and flags the bundle as `partial`,
**So that** the agent loop never hangs waiting for a slow surface and the LLM knows it is grounding on incomplete context.

**Acceptance Criteria:**

- Default timeout 800ms; configurable per-request
- `meta.partial: true` when timeout was reached
- `meta.had_vector_hits` / `meta.had_live_lookup` reflect which surfaces completed
- Sustained `partial: true` rate above 5% triggers an alert

### US-7: Sliding-window chunk coalescing (P1)

**As** an AI engineer,
**I want** transcript-chunk boundaries softened by sliding-window overlap,
**So that** an order number that straddles two 800ms chunks still makes it into the embed query.

**Acceptance Criteria:**

- Configurable overlap window (default 200ms tail of previous chunk)
- Coalescing is stateful per-conversation (keyed on `conversation_uid` if available)
- Skip coalescing if the calling agent has already pre-processed chunks

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | Bridge MUST emit a structured JSON bundle on every call, including degraded modes |
| REQ-2 | Vector search MUST run a two-stage retrieval (ANN pool + cross-encoder rerank) |
| REQ-3 | Live Podium lookup MUST run in parallel with vector search, not serial |
| REQ-4 | Hard wall-clock deadline default 800ms; never block past it |
| REQ-5 | Live fields (`LIVE_FIELDS` set) win over vector fields on merge |
| REQ-6 | Retrieval-time PII redaction applied AFTER merge, BEFORE emission |
| REQ-7 | Token budget enforced per surface, with rerank-priority drop order |
| REQ-8 | `meta.partial` flag emitted whenever any surface failed to complete |
| REQ-9 | Pgvector reference implementation provided; Pinecone / Weaviate documented |
| REQ-10 | Embedder + reranker are pluggable behind `Protocol`-typed interfaces |
| REQ-11 | Bridge MUST integrate with `podium-auth` for the live Podium lookup; never holds its own auth |
| REQ-12 | Per-contact filter (`contact_uid`) supported and pushed down to the vector store as a WHERE clause |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://api.podium.com/v4/contacts/{uid}` | GET | Live contact-state fetch for the merge step |
| pgvector (or Pinecone / Weaviate) | query | ANN retrieval over the embedded conversation corpus |
| Embedding model API | embed | Vectorize the transcript-chunk query (default local `bge-large-en-v1.5`) |
| Cross-encoder API | score | Rerank the ANN pool (default local `bge-reranker-base`) |

## Non-Goals

- This skill does not ingest into the vector store. That is the job of `podium-conversation-history-export` plus an embedding step (documented in `references/implementation.md`).
- This skill does not run the LLM. It emits a context bundle the calling agent loop assembles into a prompt.
- This skill does not implement webhook handling for the live transcript stream — that is `podium-call-transcript-pipeline`.
- This skill does not provide a UI; it is a library + scripts.
- This skill does not implement Pinecone / Weaviate adapters in code — only the reference pgvector path is shipped runnable. Adapters are documented; production rollouts plug them in.
- This skill does not handle multi-tenant routing — that is `podium-auth`'s `PodiumOrgRouter`. Each tenant gets its own bridge instance and its own vector-store table or namespace.

## Success Metrics

| Metric | Target |
|---|---|
| p95 end-to-end bridge latency | ≤ 800ms |
| p99 end-to-end bridge latency | ≤ 1200ms |
| `meta.partial: true` rate (sustained 1h average) | ≤ 5% |
| Top-1 rerank precision (human-labeled eval set) | ≥ 0.80 |
| PII leak rate (regex audit of emitted bundles) | 0 |
| Bundle-to-LLM token-budget overflow incidents per quarter | 0 |
| Live-state stale value reaching the LLM | 0 (live always wins on `LIVE_FIELDS`) |

## Constraints & Assumptions

- The calling agent loop owns the LLM and the overall prompt budget. The bridge's 1500-token default is its slice, not the total.
- The vector store is populated and reasonably fresh. If the ingest pipeline is broken, the bridge will still emit live-only bundles — that is degraded mode, not normal operation, and the operator should fix ingest.
- `podium-auth` is available and supplies the live-Podium credential. The bridge does not implement OAuth itself.
- Cross-encoder reranking adds ~200ms p99. If the model is too slow on a given deployment, the operator can swap the reranker for raw cosine score — the API surface accommodates a no-op reranker.
- Pgvector's `<=>` operator is the cosine-distance default. Other stores use their native distance functions; the adapter handles the translation.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Reranker p99 exceeds budget under load | Medium | High (degraded retrievals shipped to LLM) | Hard timeout + fallback to raw cosine; alert on sustained `partial` rate |
| Vector store falls behind ingest, stale corpus | Medium | Medium (irrelevant retrievals) | Track `occurred_at` freshness in the bundle; degrade gracefully |
| Live Podium API rate-limits the lookup surface | Medium | Medium (vector-only bundles) | Defer to `podium-rate-limit-survival` for backoff; flag in `meta` |
| PII regex misses a novel pattern | Medium | Critical (data leak to LLM) | Patterns are a defense-in-depth layer; ingest is the primary; audit logs flag suspicious tokens |
| Token budget under-allocated relative to model window | Low | Medium (excerpts dropped) | Surface `meta.dropped_excerpts_count`; operator tunes per-deployment |
| Contact_uid pre-filter excludes relevant cross-contact context | Low | Low (rare; same operator across calls) | Filter is opt-in per call; bridge accepts `contact_uid=None` for unfiltered search |
| Bridge becomes a bottleneck for the agent loop | Low | High (call quality drops) | Profile per-surface; horizontal-scale the bridge; vector-store p99 is the usual culprit |

## Educational Disclaimer

This skill ships production-grade retrieval-substrate patterns for connecting Podium to an LLM as of the date the skill was authored. Vector-store APIs, embedding models, reranker models, and Podium endpoints all evolve. Validate latency budgets, embedding dimensions, and live-API contract against your specific deployment before production rollout. PII regex patterns are a defense-in-depth layer — they are not a substitute for proper redaction at ingest time and not a compliance certification. The skill author is not responsible for breaking changes in upstream Podium behavior, model API contracts, or any data leakage that bypasses the documented patterns.
