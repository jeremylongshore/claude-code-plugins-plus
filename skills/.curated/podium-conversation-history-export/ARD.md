# ARD: Podium Conversation History Export

## Architecture Pattern

**Streaming ETL pipeline + CDC watermark store + operator CLIs.** The core is a set of async generators that crawl Podium endpoints page-by-page (cursor pagination), yield records into a streaming gzip-JSONL writer, then a separate chunking pass reads JSONL line-by-line and emits embedding-ready chunks with PII redacted. The watermark store (SQLite) tracks incremental CDC state per resource. Operator CLIs (`export_conversations.py`, `export_reviews.py`, `cdc_watermark.py`, `attachment_downloader.py`, `chunk_for_embedding.py`) wrap each stage for cron/manual invocation.

Pattern: **Resumable cursor walk + overlap-margin watermark + streaming JSONL + windowed chunking with PII redaction at emit.**

The pipeline is intentionally two-pass (export → chunk) rather than one-pass (export-and-chunk-inline). Two-pass means re-chunking a corpus when the chunker's heuristics change does NOT require re-pulling the data; the JSONL artifact is the canonical record, and the chunked output is a derived view that can be regenerated cheaply.

## Workflow

```
                ┌─────────────────────────────────────────┐
                │  schedule trigger (cron / Airflow / k8s) │
                └────────────────┬────────────────────────┘
                                 ▼
                ┌─────────────────────────────────────────┐
                │  cdc_watermark.py — load watermark      │
                │  resource: conversations|reviews|contacts│
                │  returns: last successful updated_at    │
                └────────────────┬────────────────────────┘
                                 ▼
                ┌─────────────────────────────────────────┐
                │  cursor walk                            │
                │  ├ sort: created_at:asc OR updated_at:asc│
                │  ├ limit: 100 (Podium max)              │
                │  ├ filter: updated_since = wm - margin  │
                │  ├ persist cursor after every page      │
                │  └ dedup on id / (id, updated_at)       │
                └────────────────┬────────────────────────┘
                                 ▼
                ┌─────────────────────────────────────────┐
                │  stream_export — gzip JSONL writer       │
                │  ├ separators=(",", ":")                │
                │  ├ flush every 1000 records             │
                │  └ memory: O(one record)                │
                └────────────────┬────────────────────────┘
                                 ▼
                ┌─────────────────────────────────────────┐
                │  attachment_downloader.py (parallel)     │
                │  ├ concurrency=8                        │
                │  ├ refresh-on-403 (re-fetch signed URL) │
                │  └ raise on repeat 403 (no silent skip) │
                └────────────────┬────────────────────────┘
                                 ▼
                ┌─────────────────────────────────────────┐
                │  chunk_for_embedding.py                  │
                │  ├ stream JSONL line-by-line            │
                │  ├ break on token cap OR idle gap > 24h │
                │  ├ overlap = 200 tokens                 │
                │  ├ PII redaction at emit                │
                │  └ deterministic chunk_id               │
                └────────────────┬────────────────────────┘
                                 ▼
                ┌─────────────────────────────────────────┐
                │  emit chunks → consumer's vector store  │
                │  (pgvector / Qdrant / Weaviate / etc.)  │
                └────────────────┬────────────────────────┘
                                 ▼
                ┌─────────────────────────────────────────┐
                │  advance_watermark(max_seen_updated_at) │
                │  ONLY after full pass succeeds          │
                └─────────────────────────────────────────┘
```

## Progressive Disclosure Strategy

- **SKILL.md** is the entry point. It opens with the six production failures and walks through one mitigation per failure mode in a fixed order matching the pipeline stages (crawl → CDC → attachments → chunking → redaction → streaming).
- **PRD.md** is the product framing for stakeholders justifying the work — the three personas (Dana, Priya, Hema) cover the data-engineering, AI-engineering, and compliance perspectives.
- **ARD.md** (this document) is the engineer's reference for how the pieces fit together and why the two-pass design is non-negotiable.
- **references/errors.md** is a flat lookup table — `ERR_EXPORT_001` → cause + solution — for the on-call runbook.
- **references/examples.md** is a cookbook of full worked snippets covering full crawls, incremental syncs, vector-store-specific loading, and the PII-redaction audit pattern.
- **references/implementation.md** is the language-portability layer plus vector-store-specific wiring (pgvector, Qdrant, Weaviate) and the chunk-sizing math.
- **scripts/** are executable operator tools; each is single-responsibility and prints JSON-on-stdout / human-on-stderr so they compose into shell pipelines.

## Tool Permission Strategy

```yaml
allowed-tools:
  - Read           # read config, watermark DB, JSONL exports for chunk pass
  - Write          # write JSONL exports, chunk output, attachment files
  - Edit           # edit cursor checkpoint files, watermark advances
  - Bash(curl:*)   # call Podium endpoints in shell examples and attachment refresh
  - Bash(jq:*)     # parse paginated responses in shell examples
  - Bash(python3:*) # invoke the operator scripts
  - Bash(sqlite3:*) # inspect the CDC watermark store
  - Bash(gzip:*)   # decompress JSONL exports for inspection
  - Grep           # PII pattern audits, leak-detection sweeps
```

`Bash(rm:*)` and `Bash(git:*)` are intentionally absent — this skill never deletes files (export artifacts must survive for audit) and never makes git commits. The watermark reset operation goes through `cdc_watermark.py --reset`, not raw file deletion.

## Directory Structure

```
plugins/saas-packs/podium-pack/skills/podium-conversation-history-export/
├── SKILL.md
├── PRD.md
├── ARD.md
├── config/
│   └── settings.yaml              # page size, overlap margin, concurrency, chunking thresholds
├── references/
│   ├── errors.md                  # ERR_EXPORT_001..014 with cause + solution
│   ├── examples.md                # 10 worked examples
│   └── implementation.md          # Node equivalents, vector-store wiring, chunk-sizing math
└── scripts/
    ├── export_conversations.py    # CLI: full or incremental conversation export
    ├── export_reviews.py          # CLI: full or incremental review export
    ├── cdc_watermark.py           # CLI: inspect / reset / advance watermark
    ├── attachment_downloader.py   # CLI: parallel download with refresh-on-403
    └── chunk_for_embedding.py     # CLI: chunk JSONL with PII redaction
```

## API Integration Architecture

The Podium export surface is a small set of list endpoints plus a single attachment-refresh endpoint. Each is wrapped by exactly one async generator:

| Endpoint | Method | Wrapping |
|---|---|---|
| `GET /v4/conversations` | `crawl_conversations()` | Cursor walk + dedup; consumed by `export_conversations.py` |
| `GET /v4/conversations/{id}/messages` | `crawl_messages(conv_id)` | Per-conversation expansion; streamed into JSONL |
| `GET /v4/reviews` | `crawl_reviews()` | Cursor walk + dedup; consumed by `export_reviews.py` |
| `GET /v4/contacts` | `crawl_contacts()` | Cursor walk + dedup |
| `GET /v4/attachments/{id}` | `refresh_attachment_url(att_id)` | Called only by `attachment_downloader.py` on 403 |

All HTTP calls flow through a `podium_get(path, params=...)` injected dependency that wraps `podium-auth` (for token refresh) and `podium-rate-limit-survival` (for quota survival). This skill does NOT re-implement either layer.

## Data Flow Architecture

```
[Podium API]                  [Export Process]                   [Storage]
     │                              │                                │
     │  GET /v4/conversations       │                                │
     │  ?cursor=X&sort=...          │                                │
     │  ◄────────────────────────── │                                │
     │  → 100 rows + next_cursor    │                                │
     ├─────────────────────────────►│                                │
     │                              │  for row in rows:              │
     │                              │    if row.id in seen: continue │
     │                              │    yield row                   │
     │                              ├──────────────────────────────► JSONL (gzip stream)
     │                              │                                │
     │                              │  persist cursor + seen_ids     │
     │                              ├──────────────────────────────► .cursor.json
     │                              │                                │
     │  GET /v4/attachments/{id}    │                                │
     │  (on 403 from signed URL)    │                                │
     │ ◄──────────────────────────  │                                │
     │  → fresh signed URL          │                                │
     ├─────────────────────────────►│  retry download                │
     │                              ├──────────────────────────────► attachments/
     │                              │                                │
     │                              │  on full-pass complete:        │
     │                              │  advance_watermark(max_seen)   │
     │                              ├──────────────────────────────► watermarks.sqlite
     │                              │                                │
     │                              │  --- chunking pass ---         │
     │                              │  stream JSONL line-by-line     │
     │                              │  redact PII at emit            │
     │                              ├──────────────────────────────► chunks.jsonl.gz
```

Two streaming boundaries are load-bearing:

1. Records never accumulate in memory between Podium and JSONL.
2. Records never accumulate in memory between JSONL and chunked output.

A long thread is processed in O(window-size) memory at every stage, not O(thread-size).

## Error Handling Strategy

Four error classes:

| Class | Trigger | Caller behavior |
|---|---|---|
| `PodiumExportError` (transient) | 5xx, network timeout, attachment 403 (first occurrence) | Retry with exponential backoff + jitter, max 4 attempts |
| `PodiumExportError` (cursor_invalid) | 409 `cursor_invalid` (cursor outlived its server-side anchor) | Drop cursor; restart from current watermark |
| `PodiumExportError` (permanent) | 401, 403 on data endpoints (delegate to `podium-auth`) | Surface to ops; auth layer handles re-auth |
| `WatermarkDriftError` | Loader observes a row with `updated_at < watermark` outside overlap margin | Reset watermark via `cdc_watermark.py --reset`; document the cause |

Retry policy is in `_with_retry()` in each script. Permanent errors short-circuit retry — there is no value in retrying `cursor_invalid` without first dropping the cursor.

## CDC Watermark Semantics

The watermark is a single floating-point Unix timestamp per resource. Three operations:

| Operation | Behavior | Use case |
|---|---|---|
| `get_watermark(resource)` | Returns the last successfully advanced watermark, or 0.0 if never set | Beginning of every incremental run |
| `advance_watermark(resource, ts)` | Sets the watermark to `ts`. Only called after a full pass succeeds. | End of a successful incremental run |
| `reset_watermark(resource)` | Sets the watermark to 0.0. Forces a full re-pull on next run. | Recovery from a corrupted run or a schema change |

The watermark is NEVER advanced per-page — only after the full pass completes. This is the design choice that makes a crash mid-run automatically re-pull: the watermark stays at the previous value, and the next run starts from that minus the overlap margin.

## Composability & Stacking

`podium-conversation-history-export` is the **bulk-data layer**. It depends on auth and rate-limit-survival; it is consumed by the RAG-context bridge.

```
podium-rag-context-bridge       ◄── consumes the chunked output
        │
        ▼
podium-conversation-history-export  ◄── this skill
        │
        ▼
podium-call-transcript-pipeline ◄── shares PII pattern set
        │
        ▼
podium-rate-limit-survival      ◄── delegates quota survival
        │
        ▼
podium-auth                      ◄── delegates token refresh
```

A consumer building a RAG pipeline holds (a) a `PodiumAuth` for auth and (b) a configured exporter instance; the chunk output drops directly into any vector-store loader without further transformation.

## Performance & Scalability

- **Full-export throughput**: bounded by Podium's per-org rate limits, not by this skill. Empirically: 10k conversations per hour at 8 concurrent attachment downloads and `limit=100` page size.
- **Incremental throughput**: O(delta-rows) per night. A 10k-conversation org with a 1% daily churn pulls ~100 rows per night; runtime ≤ 5 minutes including chunking.
- **Memory profile**: O(one record) at the export stage. O(window-size) at the chunk stage. A 4000-message thread does not blow heap.
- **Disk profile**: gzip-compressed JSONL averages ~3KB per conversation message. A 2-year org: 500k conversations × 20 messages × 3KB ≈ 30 GB raw, ~6 GB gzipped.
- **Cold start**: one cursor walk per resource on first run. With a 100k-conversation org and rate-limit headroom, ~10 hours to a full corpus.

## Security & Compliance

- **PII redaction at emit**: the eternal-PII problem is solved at chunk-emit time, before any record leaves the export process toward an embedding API. There is no downstream filter, no query-time redaction — the chunk written to disk is the chunk loaded into the vector store.
- **Redaction pattern set**: shared with `podium-call-transcript-pipeline` via a single Python module import. A single source of truth; updates propagate to both skills.
- **Audit field on every chunk**: `pii_redacted: true` (or `false` for chunks that bypassed redaction, which should be zero in production). A compliance audit greps the chunked corpus for `pii_redacted: false` to find any escapes.
- **Credentials**: never embedded in scripts — all auth delegated to `podium-auth`.
- **Attachment data at rest**: the operator chooses the storage target; this skill writes to a configured directory. Encryption-at-rest is the storage layer's responsibility (S3 SSE, GCS CMEK, etc.).
- **Watermark DB**: SQLite with WAL mode; mode 0600 on the file. Not encrypted at rest by default — operator's responsibility if the watermark itself is sensitive (typically it is not — it's a timestamp).

## Testing Strategy

- **Unit tests**: mock `podium_get` to return synthetic paginated bodies; verify dedup, cursor persistence, and overlap-margin behavior. Stub `time.time()` for watermark tests.
- **Integration tests**: against a Podium sandbox org with a known fixture corpus (10 conversations, 5 reviews, 3 contacts); verify full-export count matches sandbox count and a re-run produces zero new rows.
- **CDC test**: backdate a record's `updated_at` to exactly the watermark second; verify the next pull includes it (overlap margin works).
- **Attachment expiry test**: stub the first signed URL to return 403 and verify the refresh-on-403 path fires exactly once before retry succeeds.
- **Long-thread test**: synthesize a 4000-message thread fixture; verify chunker memory profile stays bounded and emits coherent chunks with idle-gap breaks.
- **Redaction test**: corpus of synthetic PII (SSN, card, address, email, phone); verify 100% match rate; verify `pii_redacted: true` on every chunk.
- **Crash-recovery test**: SIGKILL the export mid-page; verify next run resumes from the persisted cursor with no duplicate rows in the output JSONL.

## Failure-Mode Coverage Matrix

| Failure mode in overview | Mitigation in skill | Test that proves it |
|---|---|---|
| Cursor pagination drift | Stable sort + dedup on id + persist cursor per page | `test_dedup_on_midwalk_update` |
| CDC gap at watermark second | `>=` with overlap_margin + dedup on `(id, updated_at)` | `test_watermark_boundary_inclusion` |
| Attachment URL expiry | refresh-on-403 with single retry | `test_attachment_403_refresh` |
| Oversized thread chunking | Token cap + idle-gap break + overlap | `test_chunker_4000_message_thread` |
| PII embedded into vector store | Redact at chunk-emit time | `test_pii_pattern_coverage` |
| Export OOM on long thread | Streaming JSONL + O(record) memory | `test_memory_bounded_on_long_thread` |
