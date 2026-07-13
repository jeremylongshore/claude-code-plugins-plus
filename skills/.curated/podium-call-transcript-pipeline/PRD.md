# PRD: Podium Call Transcript Pipeline

## Summary

**One-liner**: Durable, idempotent ingest pipeline that consumes Podium phone-call transcripts from a webhook (or a poller fallback), reconciles partial-vs-completed events, detects language, redacts PII with an auditable log, preserves speaker diarization through chunking, and enqueues records for a downstream RAG/LLM consumer.

**Domain**: SaaS integration / conversation intelligence / SMB phone-AI assist

**Users**: Integration engineers wiring Podium into an AI-assist stack, AI engineers building the RAG layer that consumes transcripts, small-business owners whose teams answer phones with AI assistance

## Problem Statement

Mark, a campervan retailer running 12 staff across two locations, wants the phone-answering staff to get AI-generated suggestions while they talk to a caller — informed by what previous callers have asked, what was promised, and what the team's standard answers are. Podium phone calls are already transcribed by Podium, but the transcripts arrive on a webhook minutes to hours after the call ends, in chunks (`partial`, then `completed`), with caller-vs-agent speaker tags, containing PII (credit cards captured during a deposit, callback phone numbers, addresses), and sometimes in languages other than English.

A naive ingest will: (a) try to be real-time and time out, (b) overwrite the final transcript with a partial, (c) send non-English transcripts to an English-only LLM, (d) leak PII to whichever third-party LLM API the RAG layer uses, (e) lose transcripts permanently when the downstream queue is briefly unavailable, and (f) collapse the speaker structure so the LLM cannot tell the caller's words apart from the agent's.

This skill installs the production layer that prevents each of those failure modes by construction and provides a clean handoff to `podium-rag-context-bridge`.

## Target Users

### Persona 1: Integration Engineer (Ravi)

- **Role**: Builds the Podium-webhook handler and the durable ingest layer; owns ops for the pipeline end-to-end.
- **Goals**: The ingest is invisible operationally. Transcripts never go missing, even when the queue is briefly down. The on-call playbook for a stuck transcript is one page. PII redaction is auditable to whatever regulator or customer asks.
- **Pain Points**: Last month, 14 transcripts were lost overnight because the Redis cluster failed over and the webhook handler had already acked Podium. A previous version of the redactor logged the un-redacted transcript before redacting it, and the logs went to a third-party log aggregator — a 6-week cleanup followed. Partial-then-completed overwrite caused the LLM to confidently summarize a half-transcript as the whole call.
- **Technical Level**: High (async Python, SQLite/Redis/SQS fluent, comfortable with regex and spaCy).

### Persona 2: AI Engineer building the RAG layer (Priya)

- **Role**: Consumes the outbound record shape produced by this skill; builds the RAG retrieval and the LLM prompt that the on-phone agent sees.
- **Goals**: Predictable record shape. Speaker structure preserved. Language tagged at the record level so the RAG retriever can filter by language before invoking a multilingual model. No PII in the vector store, period — both for compliance and because PII fragments cause embedding-similarity garbage.
- **Pain Points**: An earlier integration concatenated all segments into one text field; the RAG layer could not answer "what did the caller specifically ask for?" because it could not separate caller turns from agent turns. PII tokens (real card numbers) ended up as nearest neighbors to other PII tokens in the embedding space — privacy bug AND retrieval-quality bug at once.
- **Technical Level**: High (RAG architecture, embedding models, prompt design).

### Persona 3: Small-business owner (the Mark archetype)

- **Role**: Runs a 12-person team across two locations. Wants AI to help the phone-answering staff give consistent, accurate answers.
- **Goals**: The phone-AI is reliably helpful. It never reads gibberish from a misdetected language. It never repeats back a credit-card number the caller said. It works on Monday mornings when 40 weekend transcripts arrive at once.
- **Pain Points**: Two prior attempts to wire AI into phone answering failed because the transcripts arrived broken (one tool dropped 30% on a busy weekend; another fed PII straight to a public LLM). Trust in AI tooling is fragile and one visible leak ends the project.
- **Technical Level**: Low (operator; does not read the code; sees the AI-assist UI the team uses).

## User Stories

### US-1: Webhook ack within latency budget (P0)

**As** an integration engineer,
**I want** the webhook handler to verify signature, durably store the raw event, and return 200 in under 250ms p95,
**So that** Podium's webhook retry logic never trips and we never lose events to handler timeout.

**Acceptance Criteria:**

- p95 handler latency ≤ 250ms (signature verify + SQLite insert + JSON response)
- Inbox insert is durable (SQLite WAL mode or equivalent) before 200 is returned
- A non-2xx response is returned if the inbox insert fails — never a 200 with a dropped event

### US-2: Partial-vs-completed reconciliation (P0)

**As** an AI engineer,
**I want** the outbound record to always carry the completed transcript, never a partial,
**So that** the LLM never summarizes a half-transcript as if it were the whole call.

**Acceptance Criteria:**

- Inbox has UNIQUE(transcript_id, event_type) — duplicate deliveries are no-ops
- `call.transcript.completed` always supersedes `call.transcript.partial` regardless of arrival order
- A `partial` event arriving after `completed` for the same transcript is logged and ignored
- The outbound record's `status` field is one of `final | failed` — never `partial`

### US-3: Language detection on ingest (P0)

**As** a small-business owner,
**I want** non-English transcripts routed to a different queue than English,
**So that** the phone-AI never feeds an Aussie agent garbage suggestions translated through an English-only model.

**Acceptance Criteria:**

- Every outbound record carries `detected_language` (ISO 639-1) and `language_confidence` (0..1)
- English with confidence ≥ 0.85 → `queue:rag.transcripts.en`
- Confidence < 0.50 → `queue:rag.transcripts.review` (human-review queue)
- All other → `queue:rag.transcripts.{lang}` (e.g. `.zh`, `.vi`, `.es`)
- Detection is deterministic across runs (seeded `DetectorFactory`)

### US-4: PII redaction with auditable log (P0)

**As** an integration engineer,
**I want** every PII redaction logged with category, rule id, and character offsets,
**So that** a privacy audit can reconstruct what was redacted from any transcript without re-running detection.

**Acceptance Criteria:**

- Redaction happens before the transcript reaches the outbound queue (not after)
- Categories covered: CREDIT_CARD (Luhn-validated), PHONE, EMAIL, SSN, ADDRESS, PERSON (when presidio available)
- Audit log is JSONL keyed by `transcript_id` with one event per redaction
- Audit log is written to a separate durable store from the redacted transcript
- A redactor failure (presidio model missing, etc.) degrades to regex-only with a per-transcript warning — never silently passes raw text through

### US-5: Durable queue write with replay (P0)

**As** an integration engineer,
**I want** the inbox to retain events until the downstream queue write succeeds,
**So that** a Redis/SQS outage never causes transcript loss.

**Acceptance Criteria:**

- Queue write happens from the processor, not from the webhook handler
- Failed queue writes increment `attempt_count` and set `next_attempt_at` per exponential backoff (max 1h)
- After 12 failed attempts (~4 days), record moves to a dead-letter table and pages on-call
- During a 1-hour downstream outage, zero events are lost; all are delivered in arrival order on recovery

### US-6: Speaker-aware chunking (P1)

**As** an AI engineer,
**I want** chunks that never split a speaker turn and that tag each chunk with its speaker set,
**So that** the RAG retriever and the LLM prompt can preserve who-said-what.

**Acceptance Criteria:**

- Chunk boundaries land at segment boundaries — never mid-utterance
- Each chunk carries `speakers: [...]` listing the speaker roles present
- Overlap between chunks is built from trailing segments of the prior chunk (token-bounded, default 200)
- Single-utterance segments longer than `target_tokens` produce one oversize chunk rather than mid-utterance splits (logged as `ERR_TXP_006`)

### US-7: Webhook-missing fallback poller (P1)

**As** an integration engineer,
**I want** a poller that detects when a `call.ended` event was never followed by a transcript event within N hours,
**So that** missing webhook deliveries do not result in permanently-missing transcripts.

**Acceptance Criteria:**

- Poller queries the conversations API since N hours ago
- For each conversation with a call and no `call.transcript.completed` in the inbox, the poller fetches the transcript directly and synthesizes an inbox row
- Synthesized rows are tagged `source=poller` to distinguish from webhook-sourced rows
- Poller is idempotent — running it twice does not double-insert

## Functional Requirements

| ID | Requirement |
|---|---|
| REQ-1 | Webhook handler must durably store events before returning 200 |
| REQ-2 | Inbox UNIQUE(transcript_id, event_type) constraint must make redelivery idempotent |
| REQ-3 | `completed` events must supersede `partial` events for the same transcript regardless of arrival order |
| REQ-4 | Language detection must be deterministic (seeded) and emit `detected_language` + `language_confidence` |
| REQ-5 | PII redaction must run before the outbound queue write and produce an auditable log |
| REQ-6 | Queue writes must be retried with exponential backoff (cap 1h, ceiling 12 attempts) |
| REQ-7 | Dead-letter rows must page on-call and never silently drop |
| REQ-8 | Chunker must never split a segment across speakers |
| REQ-9 | Fallback poller must be idempotent and tag synthesized rows |
| REQ-10 | All PII categories' detection failures must degrade visibly — never silently |

## API Integrations

| Endpoint | Method | Purpose |
|---|---|---|
| Application's `/podium/transcripts` (handler) | POST | Receive Podium webhook (call.transcript.* events) |
| `https://api.podium.com/v4/conversations` | GET | Fallback poll for transcripts when webhook missed |
| `https://api.podium.com/v4/conversations/{id}/transcript` | GET | Fetch a specific transcript directly |
| Downstream queue (Redis Streams / SQS / SQLite) | XADD / SendMessage / INSERT | Enqueue outbound record for the RAG layer |

## Non-Goals

- This skill does not implement the RAG retrieval or LLM prompt — that is `podium-rag-context-bridge`.
- This skill does not transcribe audio — Podium does that upstream.
- This skill does not provide a UI for reviewing redacted transcripts — it produces JSON.
- This skill does not translate non-English transcripts — it tags and routes; translation is the downstream consumer's job.
- This skill does not implement webhook signature verification — that is consumed from `podium-webhook-reliability`.
- This skill does not handle Podium auth — that is `podium-auth`.

## Success Metrics

| Metric | Target |
|---|---|
| Transcripts lost during a 1-hour downstream outage | 0 |
| Partial-as-final overwrites reaching the queue | 0 |
| Non-English transcripts routed to the English queue | 0 (caught by confidence threshold) |
| Webhook handler p95 latency | ≤ 250ms |
| PII detections that reach the outbound queue un-redacted | 0 |
| Time from `call.ended` to outbound queue record (median) | ≤ Podium transcript latency + 5s of pipeline overhead |

## Constraints & Assumptions

- Podium emits `call.transcript.partial` and `call.transcript.completed` events with the same `transcript_id`. If Podium changes this contract, the reconciler logic must follow.
- Transcript latency varies from minutes to hours; the pipeline is bounded only by downstream processing capacity, not by Podium latency.
- Presidio or an equivalent NER-based PII detector is preferred but not required — the regex layer is the floor.
- The downstream consumer (`podium-rag-context-bridge`) accepts the record shape documented in SKILL.md § Speaker-aware chunking.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Webhook handler latency budget breached → Podium retries → duplicate work | Medium | Low (idempotency catches it) | UNIQUE constraint on inbox; latency monitoring |
| Inbox SQLite corruption from a kill mid-write | Low | High (some events unreachable) | WAL mode + periodic VACUUM; daily backup |
| PII regex misses a novel format (e.g. AU-specific tax file number) | Medium | High (PII reaches queue) | Layered presidio + custom recognizers; quarterly redactor audit against fresh samples |
| Language detector misclassifies a short transcript as English | Medium | Medium (RAG returns nothing useful) | Confidence threshold 0.85; short transcripts routed to review queue |
| Dead-letter queue silently fills | Low | Critical (visible page never fires) | Hourly check on dead-letter row count; page if >0 for >1h |
| Speaker tags missing from upstream transcript (Podium edge case) | Low | Medium (chunker degrades to one-speaker chunks) | Default `speaker_role="unknown"`; chunker tolerates |

## Educational Disclaimer

This skill ships production-grade ingest patterns for Podium transcripts as of the date authored. Podium webhook event names, payload shapes, and the rate limits on the conversations API may change. Validate the specific event types (`call.transcript.partial`, `call.transcript.completed`) and the transcript JSON shape against the Podium developer documentation before deploying. PII regex patterns are conservative but not exhaustive — for regulated industries (healthcare, finance), pair this skill with a domain-specific PII detector and an external privacy audit.
