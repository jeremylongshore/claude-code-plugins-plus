# ARD: Podium Call Transcript Pipeline

## Architecture Pattern

**Webhook ingest + durable inbox + async processor + outbound queue.** Five components, three stages:

1. **Webhook handler** (`webhook_ingest.py`) — verify signature (consumed from `podium-webhook-reliability`), durably store the raw event in the inbox, ack 200.
2. **Reconciler** — read inbox rows, fold partial-vs-completed into a single per-transcript view.
3. **Language detector + PII redactor + chunker** — transform the reconciled transcript into the outbound record shape.
4. **Queue writer** — push outbound record to Redis Streams / SQS / SQLite-as-queue. Failures stay in the inbox with backoff.
5. **Fallback poller** (`transcript_poller.py`) — for missing-webhook recovery, polls the conversations API on a slower cadence.

Pattern: **Durable inbox with exactly-once-effective semantics via idempotency keys, ack-decoupled processing, and replayable failures.**

## Workflow

```
                   ┌────────────────────────────────────┐
                   │  Podium webhook delivery           │
                   │  POST /podium/transcripts          │
                   │  + Podium-Signature header         │
                   └────────────────┬───────────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────────┐
                   │  webhook_ingest.py                 │
                   │  1. verify_webhook(raw, sig)       │  ◄── podium-webhook-reliability
                   │  2. inbox.insert(transcript_id,    │
                   │     event_type, raw_payload)       │
                   │  3. return 200                     │
                   └────────────────┬───────────────────┘
                                    │ (decoupled)
                                    ▼
                   ┌────────────────────────────────────┐
                   │  processor loop (every N seconds)  │
                   │  SELECT pending FROM inbox         │
                   └────────────────┬───────────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────────┐
                   │  reconcile(transcript_id)          │
                   │  completed > partial > failed      │
                   └────────────────┬───────────────────┘
                                    │ (only on `completed`)
                                    ▼
                   ┌────────────────────────────────────┐
                   │  detect_language(transcript)       │
                   │  → (lang, confidence)              │
                   └────────────────┬───────────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────────┐
                   │  redact_segments(segments)         │
                   │  + audit log → redactions.jsonl    │
                   └────────────────┬───────────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────────┐
                   │  chunk_transcript(segments,        │
                   │    target=1500, overlap=200)       │
                   │  speaker-aware, never splits turns │
                   └────────────────┬───────────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────────┐
                   │  queue.enqueue(outbound_record)    │
                   │  Redis Streams / SQS / SQLite      │
                   └────────────────┬───────────────────┘
                                    │ success      │ failure
                                    ▼              ▼
                          mark processed    increment attempt_count
                                            schedule next_attempt_at

       ┌──────────────────────────────────────────────────────────────┐
       │  fallback: transcript_poller.py (every 1h)                   │
       │  for each call.ended without subsequent call.transcript.*    │
       │  within N hours, fetch transcript and synthesize inbox row   │
       └──────────────────────────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** opens with the six production failure modes; each subsequent section installs one mitigation. The order matters — ack-decoupling first, then de-dup, then language, then redaction, then durable queue, then chunking. Reading the skill top-to-bottom builds the pipeline in dependency order.
- **PRD.md** is the product framing: three personas (integration eng, AI eng, small-business owner) with concrete failure histories, US-1..US-7, FRs, success metrics, risk register.
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together — workflow diagram, tool permissions, directory layout, error strategy, composability with the other podium-pack skills, perf/scaling math, security/compliance posture, testing matrix.
- **references/errors.md** — `ERR_TXP_001..010` flat lookup table for on-call.
- **references/examples.md** — 10 fully-worked snippets, no `...` placeholders.
- **references/implementation.md** — Node.js port notes, presidio wiring, Redis/SQS/SQLite tradeoffs, dead-letter handling, AU-specific PII patterns.
- **scripts/** — four single-responsibility CLIs that compose into shell pipelines (each emits JSON on stdout, human-readable on stderr).

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read              # read config, inbox SQLite, transcript JSON, source for grep audits
  - Write             # write redacted transcripts, audit log, chunks JSON, runbook
  - Edit              # edit .gitignore for the durable-store files
  - Bash(curl:*)      # call Podium conversations API (fallback poller, examples)
  - Bash(jq:*)        # parse transcript JSON in shell examples
  - Bash(python3:*)   # invoke the operator scripts and processor loop
  - Bash(redis-cli:*) # inspect/drain the Redis Streams outbound queue
  - Grep              # audit the repo for leaked transcripts or un-redacted PII
```

`Bash(rm:*)`, `Bash(git:*)`, and `Bash(aws:*)` are intentionally absent — this skill never deletes files (replay depends on durable state), never makes git commits, and never assumes a specific cloud SDK is installed (the SQS path is documented but optional). `Bash(sqlite3:*)` is omitted because the scripts shell out to `python3` which holds the SQLite handle; an operator who wants to peek at the inbox uses Read on the database file via the Python CLI.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-call-transcript-pipeline/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml          # chunk sizes, redaction policy, queue backend, language thresholds
├── references/
│   ├── errors.md              # ERR_TXP_001..010 with cause + solution
│   ├── examples.md            # 10 worked examples
│   └── implementation.md      # Node port, presidio wiring, queue-backend tradeoffs, AU PII
└── scripts/
    ├── webhook_ingest.py      # FastAPI handler — verify + inbox insert + 200
    ├── transcript_poller.py   # CLI: poll conversations API as webhook fallback
    ├── pii_redact.py          # CLI: redact a transcript JSON + emit audit log
    └── transcript_chunker.py  # CLI: chunk a transcript with speaker-preserving overlap
```

## API Integration Architecture

| Endpoint | Method | Wrapping |
|---|---|---|
| Application's `/podium/transcripts` | POST | `webhook_ingest.py::transcript_webhook()` |
| `GET /v4/conversations` | Poller | `transcript_poller.py::list_recent_conversations()` |
| `GET /v4/conversations/{id}/transcript` | Poller | `transcript_poller.py::fetch_transcript()` |
| Redis Streams `XADD podium:transcripts:{lang}` | Queue | `queue.RedisStreamsQueue.enqueue()` |
| SQS `SendMessage` (optional) | Queue | `queue.SQSQueue.enqueue()` |
| SQLite `INSERT INTO outbox` (dev) | Queue | `queue.SQLiteQueue.enqueue()` |

All outbound HTTP calls (poller) flow through the `PodiumAuth.get_token()` provided by `podium-auth` and the rate-limit shim provided by `podium-rate-limit-survival`. The webhook handler is inbound and has no auth dependency on `podium-auth` — its auth is the HMAC signature verified by `podium-webhook-reliability`.

## Data Flow Architecture

```
[Podium]                [Webhook Handler]            [Inbox]            [Processor]        [Redactor]          [Queue]
   │                          │                        │                    │                  │                  │
   │ POST /transcripts        │                        │                    │                  │                  │
   ├─────────────────────────►│                        │                    │                  │                  │
   │                          │  verify_webhook()      │                    │                  │                  │
   │                          │  insert raw            │                    │                  │                  │
   │                          ├───────────────────────►│                    │                  │                  │
   │  ◄─── 200 OK ────────────┤                        │                    │                  │                  │
   │                          │                        │  pending row       │                  │                  │
   │                          │                        ├───────────────────►│                  │                  │
   │                          │                        │                    │  reconcile       │                  │
   │                          │                        │                    │  detect_lang     │                  │
   │                          │                        │                    │  segments        │                  │
   │                          │                        │                    ├─────────────────►│                  │
   │                          │                        │                    │                  │  redact + audit  │
   │                          │                        │                    │                  │  chunk           │
   │                          │                        │                    │  ◄───────────────┤                  │
   │                          │                        │                    │  outbound_record │                  │
   │                          │                        │                    ├──────────────────────────────────►  │
   │                          │                        │                    │  ◄── enqueue ack ─────────────────  │
   │                          │                        │  mark processed    │                                     │
   │                          │                        │  ◄─────────────────┤                                     │
```

The arrows that **must** complete before the next stage proceeds: webhook → inbox (durable), inbox → processor (only after commit), redactor → queue write (only after successful redaction + audit log write). The arrows that may retry: queue write (with backoff), poller fetch (Podium rate-limited).

## Error Handling Strategy

Three error classes mapped to outcomes:

| Class | Trigger | Caller behavior |
|---|---|---|
| Transient (retryable) | Queue write 5xx, Podium poller 429/5xx, SQLite locked | Increment `attempt_count`; backoff (cap 1h); retry on next loop |
| Permanent (drop or alert) | Malformed transcript JSON, missing `transcript_id`, redactor crash on bad encoding | Move to dead-letter; page on-call; never silently drop |
| Operational (visible warning) | Presidio unavailable → regex-only mode, short transcript → review queue, language confidence < 0.5 | Log structured warning; pipeline continues; metric increments |

The dead-letter table is `inbox_deadletter` and rows are inserted by the processor when `attempt_count > 12`. A separate alert rule fires when `count(*) FROM inbox_deadletter WHERE created_at > now() - 1h > 0`.

## Composability & Stacking

`podium-call-transcript-pipeline` is the **transcript-ingest layer**. It consumes three foundational skills and feeds two downstream consumers:

```
                podium-rag-context-bridge        podium-conversation-history-export
                          │                                   │
                          └────────────┬──────────────────────┘
                                       │ (consume outbound record shape)
                                       ▼
                  podium-call-transcript-pipeline   ◄── this skill
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
   podium-webhook-reliability   podium-rate-limit-survival   podium-auth
              │                        │                        │
              └────────────────────────┴────────────────────────┘
                                       │
                                       ▼
                                   Podium API
```

Consumers (`podium-rag-context-bridge`, `podium-conversation-history-export`) bind to the outbound record shape documented in SKILL.md § Speaker-aware chunking. Foundations (`podium-auth`, `podium-webhook-reliability`, `podium-rate-limit-survival`) are imported by reference — this skill never re-implements their concerns.

## Performance & Scalability

- **Webhook handler throughput**: bounded by SQLite WAL write latency (~1–5ms per insert on local disk). p95 budget of 250ms includes signature verify (~5ms) + insert + JSON response with headroom. A single handler instance handles ~200 webhooks/sec; horizontal scale is trivial because the inbox is the only shared state.
- **Processor throughput**: dominated by redaction. Regex-only: ~5ms per segment. Presidio + spaCy: ~50–200ms per segment depending on segment length. A 10-minute call (≈60 segments) takes 0.3s (regex) to 12s (presidio) of processor time. For a small business (Mark's case, ~50 calls/day), single-process is sufficient with margin.
- **Queue throughput**: Redis Streams: ~50k XADD/sec on local; SQS: ~3k/sec; SQLite outbox: ~5k/sec on WAL. The pipeline is processor-bound, never queue-bound.
- **Inbox size**: ~5KB per event (raw payload + metadata). At 50 calls/day with avg 3 events/call (ended, partial, completed) = 150 rows/day = 55k/year. SQLite handles this trivially for years before vacuuming is necessary.
- **Dead-letter handling**: at 12-attempt ceiling with exponential backoff, a row spends ~4 days in retry purgatory before dead-letter. The 1-hour dead-letter alert fires before any meaningful data backlog accumulates.

## Security & Compliance

- **PII at rest in inbox**: the raw payload stored in the inbox is **un-redacted** by design — redaction happens on the processing path. The inbox SQLite file must be encrypted at rest (filesystem-level encryption or SQLite encryption extension) and have mode 0600 ownership. The processor deletes inbox rows older than `inbox_retention_days` (default 7) after they reach `processed_at`.
- **PII in transit**: the queue write transmits the **redacted** record. Even so, TLS to Redis/SQS is required.
- **Audit log integrity**: the redactions.jsonl audit log is append-only — every redaction event is written and never modified. For regulated industries, sign each line with HMAC-SHA256 keyed by a dedicated audit key.
- **Webhook signature**: verified via `podium-webhook-reliability`. Never trust an unsigned event.
- **Outbound queue contents**: redacted transcripts only. Verify via the test in the Testing Strategy section — a CI gate that asserts no raw PII patterns reach the queue.
- **Logging**: structured JSON with `transcript_id` and metadata. Never log the redacted transcript body. Never log the pre-redaction body, period.

## Testing Strategy

| Test | Type | What it proves |
|---|---|---|
| `test_webhook_durable_before_ack` | unit | A SIGKILL between `inbox.insert` and the 200 response leaves the row visible to the processor (or the row absent and Podium will retry) |
| `test_idempotent_redelivery` | unit | Two POSTs with the same (transcript_id, event_type) produce exactly one row |
| `test_completed_supersedes_partial` | unit | `partial` arriving after `completed` does not overwrite |
| `test_language_detection_deterministic` | unit | Same input → same `(lang, confidence)` across 100 runs |
| `test_short_transcript_routes_to_review` | unit | Transcripts < 20 chars go to `queue:rag.transcripts.review` |
| `test_luhn_validated_card_redaction` | unit | `4111-1111-1111-1111` redacted; `4111-1111-1111-1112` (invalid Luhn) not |
| `test_pii_never_reaches_queue` | integration | Fuzz-test inputs with PII; assert queue messages contain no matches against PII regex |
| `test_queue_failure_retries_with_backoff` | unit | Mock queue to fail 3x; verify `attempt_count` and `next_attempt_at` progression |
| `test_dead_letter_after_12_attempts` | unit | 13th failure moves row to `inbox_deadletter` and emits alert |
| `test_chunker_never_splits_speaker_turn` | unit | Property test over random segment streams; assert chunk boundaries land between segments |
| `test_chunker_preserves_overlap` | unit | Last N tokens of chunk K-1 appear as first segments of chunk K |
| `test_poller_idempotent` | integration | Two consecutive poller runs over the same window produce no duplicate inbox rows |
| `test_presidio_unavailable_degrades_visibly` | unit | Disable presidio; verify regex-only mode runs and emits warning |
| `test_inbox_retention_drops_processed_rows` | unit | After `inbox_retention_days`, processed rows are deleted; unprocessed rows are retained |
