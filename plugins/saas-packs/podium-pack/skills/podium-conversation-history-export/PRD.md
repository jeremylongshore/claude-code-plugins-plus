# PRD: Podium Conversation History Export

## Summary

**One-liner**: Production-grade bulk + incremental exporter that turns a Podium organization's ~2 years of conversations, reviews, and contacts into a vector-store-ready corpus — cursor-paginated full crawls, `updated_at`-watermarked CDC, attachment-URL refresh-on-403, windowed semantic chunking, PII redaction before embedding, and streaming JSONL output that does not OOM on long threads.

**Domain**: SaaS data engineering / RAG pipelines / SMB customer-engagement knowledge bases

**Users**: Data engineers, AI/ML engineers building embedding pipelines, compliance officers reviewing what gets embedded

## Problem Statement

Mark Kofahl (Bonefish RV) put the requirement in one sentence: "we have about two years of knowledge in there." That knowledge — every customer thread, every review response, every contact note — sits behind Podium's REST API as paginated cursors. There is no bulk-export endpoint, no S3 dump, no `mongodump` equivalent. To embed that knowledge into a vector store for RAG, an integration must crawl it via the conversation, review, and contact list endpoints, page by page, and keep it current via incremental CDC.

Naive implementations fail in six production-reproducible ways. Cursor walks duplicate or skip records when conversations are updated mid-walk. `updated_at`-watermark CDC misses writes at the watermark second. Attachment URLs expire mid-export and produce 403s. Long threads blow embedding token budgets or OOM the export process. PII gets embedded into a corpus that is, for practical purposes, eternal — once a customer's SSN is in the index, recall requires recomputing every vector.

This skill provides the export pipeline that prevents each failure mode by construction.

## Target Users

### Persona 1: Data Engineer (Dana)

- **Role**: Owns the data pipeline that lands Podium history in the analytics warehouse and the vector store.
- **Goals**: Idempotent re-runnable exports; clear watermark semantics; one-line cron entry for incremental sync; observable failure modes (counts in / counts out, watermark advancement, errors per resource).
- **Pain Points**: A previous "quick script" produced duplicate records and a corrupted cursor file; the export OOM'd on a single 4000-message thread and took down the analytics box for an afternoon; nobody noticed the watermark hadn't advanced for three weeks.
- **Technical Level**: High (async Python, SQL, comfortable with CDC patterns, knows what idempotency means).

### Persona 2: AI Engineer (Priya)

- **Role**: Builds the embedding pipeline that reads the exported corpus, computes vectors, and loads them into pgvector/Qdrant/Weaviate.
- **Goals**: Chunks that are coherent (one chunk = one semantic unit, not a random 1500-token slice); deterministic chunk IDs so re-embedding is incremental; PII redaction guaranteed at chunk-emit, not best-effort.
- **Pain Points**: An earlier RAG pilot embedded raw PII because redaction lived in a downstream filter and was bypassed in a refactor; chunk boundaries cut mid-message and produced poor retrieval quality on the long-thread case; re-embedding the full corpus to fix one bug cost a month of vector-store API spend.
- **Technical Level**: High (ML eng; sometimes asks "why does Dana's pipeline emit chunks instead of raw messages?").

### Persona 3: Compliance Officer (Hema)

- **Role**: Reviews what data leaves the customer's tenant boundary into third-party systems (the embedding API, the vector store).
- **Goals**: Verifiable PII-redaction guarantee at export time; an audit log of what was redacted vs not; the ability to point at a specific commit and say "this redaction policy was in effect for this run."
- **Pain Points**: A prior vendor's "redact PII" feature was applied at query time, not embedding time — the eternal-PII problem. The audit log was structured-but-incomplete; tracking down what was redacted in a specific six-week window required reconstructing logs from gzipped archives.
- **Technical Level**: Medium (reads code, comfortable with policy-as-code; does not write pipelines).

## User Stories

### US-1: Resumable cursor-paginated full crawl (P0)

**As** a data engineer,
**I want** the full historical crawl to persist its cursor after every page and dedup on row id,
**So that** a process crash mid-crawl resumes at the last good page boundary without duplicating records.

**Acceptance Criteria:**

- Cursor and seen-id set are persisted to disk after every successful page
- A `SIGKILL` mid-page does not duplicate any row in the output JSONL
- A row updated mid-crawl is yielded exactly once (the first sighting wins)
- `seen_ids` cache is bounded to last 50k IDs to prevent unbounded memory growth

### US-2: Overlap-margin CDC watermark (P0)

**As** a data engineer,
**I want** incremental syncs to use `updated_at >= (watermark - overlap_margin)` and dedup,
**So that** writes happening exactly at the watermark second are never missed.

**Acceptance Criteria:**

- Default `overlap_margin_seconds = 60`
- Watermark advances only after a full pass completes successfully
- A partial pass (crash mid-pass) re-pulls from the previous watermark on retry
- Loader dedups on `(id, updated_at)` to absorb the overlap re-pull volume

### US-3: Attachment URL refresh on 403 (P0)

**As** a data engineer,
**I want** the attachment downloader to detect a 403, fetch a fresh signed URL, and retry,
**So that** multi-hour exports do not lose attachments to URL expiry.

**Acceptance Criteria:**

- 403 response triggers a `GET /v4/attachments/{id}` and a single retry
- Repeated 403 after refresh raises (no infinite retry loop)
- Parallel downloads honor a concurrency cap (default 8)
- Partial downloads (interrupted mid-file) are re-fetched, not patched

### US-4: Semantic-boundary chunking (P1)

**As** an AI engineer,
**I want** chunks to break on natural boundaries (turn boundaries, idle gaps > 24h, token cap),
**So that** retrieved chunks carry coherent context, not arbitrary 1500-token slices.

**Acceptance Criteria:**

- Default `target_tokens = 1500`, `overlap_tokens = 200`
- Force-break on idle gap > 24h between consecutive messages
- Chunk overlap carries last ~`overlap_tokens` of messages from the previous chunk
- Each chunk emits a deterministic `chunk_id` (`source_id:start_msg_id:end_msg_id`) so re-chunking is reproducible

### US-5: PII redaction before embedding (P0)

**As** a compliance officer,
**I want** the same redaction pattern set as `podium-call-transcript-pipeline` applied at chunk-emit time,
**So that** PII never reaches the embedding API or the vector store.

**Acceptance Criteria:**

- Redaction runs on chunk body + display names + reproduced attachment filenames
- Redacted output uses unambiguous placeholders (`[REDACTED_SSN]`, etc.) — never blank/empty strings
- A `pii_redacted: true` field is emitted on every chunk that passed through redaction
- The pattern set is the same module imported by `podium-call-transcript-pipeline` (single source of truth)

### US-6: Streaming JSONL output (P0)

**As** a data engineer,
**I want** records written one-per-line to a gzip stream, never held in memory in bulk,
**So that** a 4000-message thread does not OOM the export host.

**Acceptance Criteria:**

- Memory cost is O(one record) at the export stage
- Memory cost is O(window-size) at the chunking stage, not O(thread-size)
- Output is `.jsonl.gz` with `separators=(",", ":")` and a flush every 1000 records
- A crash bounds data loss to one flush interval (~1000 records)

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | Cursor walk must persist `cursor + seen_ids` after every successful page |
| REQ-2 | CDC pull must use `updated_at >= (watermark - overlap_margin)` with loader-side dedup on `(id, updated_at)` |
| REQ-3 | Attachment downloader must refresh signed URL on 403 and retry exactly once |
| REQ-4 | Chunker must break on token cap AND on idle gap > 24h, with configurable overlap |
| REQ-5 | PII redaction must run at chunk-emit time, before any embedding API call |
| REQ-6 | Output must be gzip-compressed JSONL, streamed, with bounded crash-loss window |
| REQ-7 | Watermark store must support inspect / reset / manual-advance via `cdc_watermark.py` |
| REQ-8 | All HTTP calls must delegate auth to `podium-auth` and rate-limit to `podium-rate-limit-survival` (no re-implementation) |
| REQ-9 | Chunk IDs must be deterministic for re-embedding idempotency |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| `https://api.podium.com/v4/conversations` | GET | List conversations (cursor + `updated_since` filters) |
| `https://api.podium.com/v4/conversations/{id}/messages` | GET | List messages for a conversation (cursor-paginated) |
| `https://api.podium.com/v4/reviews` | GET | List reviews (cursor + `updated_since` filters) |
| `https://api.podium.com/v4/contacts` | GET | List contacts (cursor + `updated_since` filters) |
| `https://api.podium.com/v4/attachments/{id}` | GET | Re-fetch a fresh pre-signed URL for an attachment |

## Non-Goals

- This skill does not implement OAuth — that is `podium-auth`. The exporter assumes a `PodiumAuth` instance is provided.
- This skill does not implement rate-limit survival — that is `podium-rate-limit-survival`. The exporter assumes the calling layer obeys quotas.
- This skill does not embed text into vectors — that is the downstream pipeline. The output is chunked JSONL; embedding is the consumer's problem.
- This skill does not load chunks into a specific vector store — Pinecone vs Qdrant vs pgvector is a deployment choice. `references/implementation.md` shows wiring for all three.
- This skill does not provide a UI — it is scripts + a library, not a console.

## Success Metrics

| Metric | Target |
|---|---|
| Full-export duplicate-record rate | 0 (dedup on id) |
| CDC missed-write rate (writes at watermark boundary) | 0 (overlap margin closes the gap) |
| Attachment download failure rate from URL expiry | 0 (refresh-on-403) |
| Chunks with mid-message cuts | 0 (semantic boundary chunker) |
| PII leakage to vector store (manual audit) | 0 |
| Export-host OOM rate on 4000+ message threads | 0 (streaming JSONL) |
| Median incremental sync runtime for nightly delta (10k-conversation org) | ≤ 5 minutes |

## Constraints & Assumptions

- Podium's `updated_at` granularity is one second; the 60s overlap margin is conservative against that.
- Podium documents `limit=100` as the cursor page-size cap; do not exceed.
- Pre-signed attachment URLs expire on the order of 15 minutes (empirically; not documented exactly).
- A typical 2-year RV-dealer Podium org has 50k–500k conversations, 10k–50k reviews, 5k–20k contacts. Sizing assumes that range.
- The vector store is the consumer's choice; this skill emits a neutral chunked-JSONL format.
- The PII pattern set is shared with `podium-call-transcript-pipeline` (single source of truth).

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Mid-walk row update causes silent skip | Medium | High (corpus gaps) | Sort by stable `created_at:asc`; dedup on id; persist seen_ids |
| Watermark advances past a partial-run failure | Medium | High (permanent CDC gap) | Advance watermark only after full-pass success; overlap margin on next run |
| Attachment URL expiry produces silent partial corpus | High | Medium (missing attachments) | Refresh-on-403; raise on repeat 403 (no silent skip) |
| Chunker boundaries split semantic units | Medium | Medium (poor retrieval) | Idle-gap force-break; overlap window; deterministic chunk IDs |
| PII leakage to vector store | Low (with redaction) | Critical | Redact at chunk-emit; share pattern set with call-transcript pipeline |
| Export OOM on long thread | High (without streaming) | High (host outage) | Streaming JSONL; O(record) memory; flush every 1000 records |
| Watermark DB corruption | Low | High (forces full re-pull) | SQLite WAL mode; `cdc_watermark.py --reset` documented escape hatch |

## Educational Disclaimer

This skill ships production-grade export and CDC patterns for the Podium API as of the date the skill was authored. Cursor pagination semantics, attachment URL expiry windows, and `updated_at` granularity are observed behaviors from production integrations; Podium may change them. Validate the specific timeouts, page sizes, and endpoint URLs against the Podium developer documentation before deploying. The PII redaction patterns are best-effort regex matches and do not constitute a HIPAA/PCI-compliant redaction guarantee — pair with downstream compliance review and a human-in-the-loop sample audit before production embedding.
