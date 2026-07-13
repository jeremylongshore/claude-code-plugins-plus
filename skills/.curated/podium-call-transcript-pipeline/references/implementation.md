# Implementation Reference — podium-call-transcript-pipeline

Language-portability, queue-backend tradeoffs, presidio wiring, AU-specific PII recognizers, and the dead-letter handling runbook.

## Node.js / TypeScript port notes

The Python pipeline translates directly to TypeScript with three notable changes:

1. **SQLite driver** — use `better-sqlite3` (synchronous, fast, WAL-friendly) rather than the async sqlite3 driver. The webhook handler does not need async sqlite when the writes are sub-millisecond.
2. **Language detection** — `franc` (small, MIT) is the closest analogue to `langdetect`. For higher accuracy, run the `fasttext-langdetect` model via a small Python sidecar invoked over a Unix socket.
3. **PII redaction** — `presidio-analyzer-node` exists but is less mature than the Python package. The pragmatic choice for a Node-only stack is the regex layer plus a Python sidecar for the NER detections; the IPC overhead is amortized across batched segments.

```typescript
import Database from "better-sqlite3";
import { createHash, createHmac, timingSafeEqual } from "crypto";

const db = new Database("podium_transcripts.db");
db.pragma("journal_mode = WAL");
db.exec(`
  CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    received_at   REAL NOT NULL,
    raw_payload   BLOB NOT NULL,
    processed_at  REAL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL,
    last_error    TEXT,
    UNIQUE(transcript_id, event_type)
  );
`);

const insert = db.prepare(
  "INSERT OR IGNORE INTO inbox(transcript_id, event_type, received_at, raw_payload) VALUES (?, ?, ?, ?)"
);

export function ingest(transcriptId: string, eventType: string, raw: Buffer): void {
  insert.run(transcriptId, eventType, Date.now() / 1000, raw);
}
```

## Queue-backend tradeoff matrix

| Backend | Throughput | Durability | Replay | Best for |
|---|---|---|---|---|
| Redis Streams | ~50k/s local | Configurable (AOF) | Built-in (XRANGE) | Single-region, mid-volume, low ops overhead |
| AWS SQS | ~3k/s/queue | 14-day retention | Built-in (visibility timeout + redrive) | Multi-region, enterprise compliance posture |
| SQLite (outbox) | ~5k/s WAL | Local disk | Trivial SELECT | Dev, small business, single-host deploys |
| Kafka | ~100k/s/cluster | Configurable retention | Built-in (offset rewind) | Multi-consumer, high-volume, complex topology |

For Mark's case (12 staff, ~50 calls/day, single VPS), SQLite-as-queue is sufficient and removes Redis as an operational dependency. The Redis path is documented as the recommended default because the canonical Intent Solutions VPS already runs Redis for other services.

## Presidio wiring

```python
# Optional dependency — degrade to regex-only on import failure.
try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

def build_analyzer():
    if not PRESIDIO_AVAILABLE:
        return None
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    # Custom recognizers (AU TFN, NZ IRD, AU Medicare) registered here.
    analyzer = AnalyzerEngine(registry=registry, supported_languages=["en"])
    return analyzer

def redact_segment_presidio(analyzer, text: str) -> tuple[str, list[dict]]:
    if analyzer is None:
        return text, []
    results = analyzer.analyze(text=text, language="en")
    # Convert presidio RecognizerResult into the skill's Redaction shape.
    redactions = [
        {"category": r.entity_type, "rule_id": f"presidio:{r.entity_type.lower()}",
         "start": r.start, "end": r.end, "score": r.score}
        for r in results if r.score >= 0.6
    ]
    # Apply redactions in reverse order to keep offsets stable.
    out = text
    for r in sorted(redactions, key=lambda r: r["start"], reverse=True):
        out = out[:r["start"]] + f"[REDACTED:{r['category']}]" + out[r["end"]:]
    return out, redactions
```

Wire presidio after the regex pass. Union the redaction lists into a single audit log. For a transcript that has both a credit card and a person name in the same sentence, the regex layer redacts the card (high precision, Luhn-validated) and presidio redacts the name (lower precision, NER-based).

## Custom recognizers for AU/NZ markets

For Mark's case (Australia), the following recognizers should be added beyond the default categories:

| Category | Pattern | Validator |
|---|---|---|
| AU_TFN | `\b\d{3}\s?\d{3}\s?\d{2,3}\b` | 11-mod weighted checksum (8 or 9 digit) |
| AU_MEDICARE | `\b\d{4}\s?\d{5}\s?\d\s?/?\s?\d?\b` | 11-mod weighted checksum (10 digit) |
| AU_PHONE | `\+?61\s?\d\s?\d{4}\s?\d{4}` | Length + leading digit validation |
| AU_POSTCODE | `\b(0[28]\d{2}\|[1-9]\d{3})\b` | State-prefix range check (NSW 1000-2999, etc.) |
| NZ_IRD | `\b\d{2,3}-?\d{3}-?\d{3}\b` | 11-mod weighted checksum |
| NZ_POSTCODE | `\b\d{4}\b` (context-sensitive) | Requires NZ address context |

Register via `register_recognizer(category, rule_id, pattern, validator)` as shown in `examples.md` § 7.

## Dead-letter handling runbook

When `inbox_deadletter` rows appear, the operator runbook is:

1. **Triage**: `SELECT id, transcript_id, event_type, last_error, attempt_count FROM inbox_deadletter ORDER BY id DESC LIMIT 50;`
2. **Classify**:
   - Queue connectivity issue → fix infrastructure, then bulk-replay
   - Malformed payload → investigate Podium-side change; do NOT replay until shape is understood
   - Redactor crash → check presidio model availability; fix and replay
3. **Replay**:

   ```sql
   INSERT INTO inbox(transcript_id, event_type, received_at, raw_payload)
   SELECT transcript_id, event_type, received_at, raw_payload
   FROM inbox_deadletter WHERE id IN (?, ?, ...);
   DELETE FROM inbox_deadletter WHERE id IN (?, ?, ...);
   ```

4. **Verify**: the processor's next pass should pick up the replayed rows and successfully enqueue them. Confirm via `SELECT * FROM inbox WHERE id IN (?,...) AND processed_at IS NOT NULL`.
5. **Document**: every replay event is logged with operator id, replayed row count, and root-cause classification. The dead-letter table is never silently emptied.

## Inbox retention and vacuuming

The processor deletes inbox rows older than `inbox.retention_days` (default 7) only after they reach `processed_at`. Unprocessed rows are retained indefinitely — they represent unresolved work and must never be dropped silently.

```sql
DELETE FROM inbox
WHERE processed_at IS NOT NULL
  AND processed_at < strftime('%s','now') - (7 * 86400);
VACUUM;
```

Run nightly via cron. The VACUUM is essential — without it, SQLite's WAL file grows unbounded.

## Webhook handler resilience patterns

Two patterns that make the webhook handler robust beyond the basic verify-then-insert:

1. **Per-request timeout** — the handler must have a hard timeout (uvicorn `--timeout-keep-alive 30`) so a slow `inbox.insert` does not hold the connection past Podium's webhook timeout. If insert latency spikes, return 5xx and let Podium retry.

2. **Process pool sizing** — uvicorn workers should be 2 × CPU cores, not 1. SQLite WAL handles concurrent writers well, and the worker is mostly I/O bound (signature verify + small insert). Under-provisioned workers cause connection queueing that pushes p95 latency over budget.

## Library packaging

This skill ships the pipeline modules inline in `SKILL.md` and `references/examples.md`. The rationale is the same as `podium-auth` — the modules are small (~600 LOC across inbox, processor, redactor, chunker), every deployment customizes the secret-store binding and queue backend, and an extracted package would require versioning that adds maintenance overhead without enabling reuse. Promote to `@intentsolutions/podium-transcripts` only when three concrete callers depend on identical behavior.

## Testing matrix (what `tests/` should cover when integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_webhook_durable_before_ack` | unit | SIGKILL between insert and 200 leaves the row visible OR absent (never half-written) |
| `test_idempotent_redelivery` | unit | Duplicate (transcript_id, event_type) is a no-op via UNIQUE constraint |
| `test_completed_supersedes_partial` | unit | Reconciler promotes completed; partial-after-completed is ignored |
| `test_language_detection_deterministic` | unit | Same input → same (lang, confidence) across 100 runs |
| `test_short_transcript_routes_to_review` | unit | <20 char transcripts route to review queue |
| `test_luhn_validated_card_redaction` | unit | Valid Luhn redacted; invalid Luhn left in place (avoids false positives on order numbers) |
| `test_pii_never_reaches_queue` | integration | Fuzz inputs with PII; assert outbound record contains no matches |
| `test_queue_failure_retries_with_backoff` | unit | Mock queue to fail; verify attempt_count and next_attempt_at progression |
| `test_dead_letter_after_max_attempts` | unit | 13th failure moves row to inbox_deadletter |
| `test_chunker_never_splits_speaker_turn` | property | 1000 random segment streams; chunk boundaries land between segments |
| `test_chunker_overlap_preserved` | unit | Last N tokens of chunk K-1 appear as first segments of chunk K |
| `test_poller_idempotent` | integration | Two consecutive runs over same window → no duplicate inbox rows |
| `test_presidio_unavailable_degrades_visibly` | unit | Disable presidio; verify regex-only mode emits warning |
| `test_inbox_retention_drops_processed_rows` | unit | After retention_days, processed rows are deleted; unprocessed retained |
| `test_au_tfn_custom_recognizer` | unit | Valid TFN redacted; invalid (failed checksum) passed through |
