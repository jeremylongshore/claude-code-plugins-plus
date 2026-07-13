# Errors — podium-conversation-history-export

Lookup table for `ERR_EXPORT_*` codes raised by the library and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_EXPORT_001 — cursor_invalid

- **HTTP**: 409 from `GET /v4/conversations` (or any list endpoint) when a previous cursor is passed
- **Cause**: The cursor's server-side anchor (typically a row that has been deleted or whose sort key has changed) is no longer valid. Common after long pauses between pages or after a Podium-side schema change.
- **Detection**: Response body contains `{"error": "cursor_invalid"}` or `{"error": "invalid_pagination"}`.
- **Action**: Delete the cursor checkpoint file (`.cursor.<resource>.json`); restart the run. Incremental runs will re-pull from the watermark; full runs will restart from page 1.

## ERR_EXPORT_002 — watermark_drift

- **HTTP**: N/A (local consistency check)
- **Cause**: The loader observed a row whose `updated_at` is older than `watermark - overlap_margin`. Indicates either a clock-skew anomaly on the Podium side or a misconfigured overlap margin.
- **Detection**: Raised in the incremental pull loop when a row passes the dedup filter but lands outside the overlap window.
- **Action**: Log and continue (the row is included in the output via the overlap-margin re-pull). If drift persists across multiple runs, raise `overlap_margin_seconds` in the config and run `cdc_watermark.py --reset` for the affected resource.

## ERR_EXPORT_003 — attachment_url_expired_repeat

- **HTTP**: 403 from a pre-signed attachment URL after a refresh attempt
- **Cause**: The pre-signed URL was refreshed via `GET /v4/attachments/{id}` but the new URL also returned 403. Indicates an upstream Podium issue (the attachment is genuinely inaccessible, not just expired).
- **Detection**: `attachment_downloader.py` sees 403 after a single refresh retry.
- **Action**: Log the attachment id; continue with the rest of the export. Do NOT loop. After the run completes, build a missing-attachments report and contact Podium support if the count is non-zero.

## ERR_EXPORT_004 — cursor_checkpoint_corrupt

- **HTTP**: N/A (local file I/O)
- **Cause**: The cursor checkpoint file exists but is not valid JSON (truncated write, disk corruption, manual edit).
- **Detection**: `json.loads()` raises on the checkpoint file at the start of a run.
- **Action**: Delete the corrupt file; restart the run. Incremental runs will re-pull from the watermark; full runs restart from page 1. Document the cause if it recurs — repeated corruption indicates a filesystem-level issue.

## ERR_EXPORT_005 — watermark_db_locked

- **HTTP**: N/A (SQLite)
- **Cause**: Concurrent processes attempted to advance the watermark for the same resource simultaneously, and SQLite's WAL lock blocked one.
- **Detection**: SQLite raises `OperationalError: database is locked`.
- **Action**: Two exporters running concurrently for the same resource is unsupported. Confirm only one cron entry / one orchestration job exists per resource. If concurrent runs are intentional (e.g., backfill + nightly), serialize via an external lock (flock, etcd, Redis SET NX).

## ERR_EXPORT_006 — chunk_pii_pattern_error

- **HTTP**: N/A (chunker)
- **Cause**: A PII regex pattern raised an exception during chunk emit (typically a regex catastrophic-backtracking timeout on a pathological message body).
- **Detection**: `chunk_for_embedding.py` catches the exception and, with `fail_on_pattern_error: true`, raises.
- **Action**: Do NOT emit the chunk. Log the offending source message id. Patch the pattern to bound backtracking (use `re2` for production-critical paths) or skip the message via an explicit deny-list.

## ERR_EXPORT_007 — chunk_token_estimate_overflow

- **HTTP**: N/A (chunker)
- **Cause**: A single message body exceeds the `target_tokens` cap. The chunker cannot split mid-message (semantic boundary requirement) so the chunk emits as oversized.
- **Detection**: Chunker emits a chunk whose `token_estimate` exceeds `target_tokens`.
- **Action**: Log a warning with the source message id. Decide downstream: either raise `target_tokens` in config, or pre-split the message body via a sentence-boundary splitter before chunk-pass. Do NOT silently truncate — that drops content.

## ERR_EXPORT_008 — export_oom_on_thread

- **HTTP**: N/A (host)
- **Cause**: The export process attempted to load a full thread into memory (regression in the streaming code path) and the host's RAM is exhausted.
- **Detection**: OOM killer terminates the process; cgroup limit exceeded; or explicit MemoryError.
- **Action**: This should not happen if the streaming path is intact. Audit the call site that built a list of messages instead of iterating an async generator. Run `test_memory_bounded_on_long_thread` to reproduce.

## ERR_EXPORT_009 — incremental_pull_partial_advance

- **HTTP**: N/A (workflow)
- **Cause**: An incremental pull was interrupted mid-pass but the watermark advanced (violates `advance_only_on_full_pass`).
- **Detection**: Manual inspection during a postmortem — the watermark is newer than the last fully completed pass.
- **Action**: Reset the watermark via `cdc_watermark.py --reset --resource <res>` and re-run. Audit the script for any premature watermark write (only the very last line after the iterator drains should advance the watermark).

## ERR_EXPORT_010 — attachment_partial_download

- **HTTP**: 200 but truncated
- **Cause**: Download interrupted mid-stream (network drop, host shutdown); the partial file is on disk with the wrong size.
- **Detection**: File size does not match `Content-Length` from the GET response.
- **Action**: Delete the partial file; re-fetch from scratch. Resume-by-Range is not used because the pre-signed URL TTL makes range-resume unreliable.

## ERR_EXPORT_011 — rate_limit_inherited

- **HTTP**: 429 from any list endpoint
- **Cause**: The org's per-endpoint quota is exceeded. The exporter is the most rate-limit-aggressive workload in the pack.
- **Detection**: `podium-rate-limit-survival` catches and surfaces as `ERR_RATE_LIMIT_*` per its own taxonomy.
- **Action**: This skill delegates to `podium-rate-limit-survival`. Tune that skill's per-endpoint quotas before the exporter runs; do not patch around it in this skill.

## ERR_EXPORT_012 — pii_pattern_set_missing

- **HTTP**: N/A (import error)
- **Cause**: The PII patterns module (`podium_pii.patterns`) is not importable. Indicates `podium-call-transcript-pipeline` is not installed or the module path was renamed.
- **Detection**: `ImportError` on chunker startup.
- **Action**: Install `podium-call-transcript-pipeline` in the same Python environment (it owns the pattern set — this skill does not fork it). Confirm via `python3 -c "from podium_pii import patterns; print(patterns.__file__)"`.

## ERR_EXPORT_013 — chunk_id_collision

- **HTTP**: N/A (chunker integrity check)
- **Cause**: Two chunks produced the same deterministic `chunk_id` — implies overlapping message ranges across chunks (a bug in the chunker's range tracking).
- **Detection**: Optional integrity pass that hashes all chunk_ids and asserts uniqueness.
- **Action**: Run the integrity pass with `--strict`. If a collision is reproducible, file an issue with the source thread fixture; do NOT load colliding chunks into the vector store (collisions corrupt similarity search).

## ERR_EXPORT_014 — watermark_reset_unauthorized

- **HTTP**: N/A (cli safety check)
- **Cause**: `cdc_watermark.py --reset` invoked without `--confirm`. Reset forces a full re-pull which can take hours and burn rate-limit budget.
- **Detection**: CLI safety check at the start of `--reset` action.
- **Action**: Re-invoke with `--confirm` if a full re-pull is intended. Document the reason in the run log so the postmortem can correlate with the data-engineering team's expectations.
