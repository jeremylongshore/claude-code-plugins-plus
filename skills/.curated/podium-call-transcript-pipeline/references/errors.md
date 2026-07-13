# Errors — podium-call-transcript-pipeline

Lookup table for `ERR_TXP_*` codes raised by the pipeline. Each entry: cause, detection point, and action.

## ERR_TXP_001 — partial_after_completed_ignored

- **Source**: Reconciler
- **Cause**: A `call.transcript.partial` event arrived after a `call.transcript.completed` was already promoted to final for the same `transcript_id`.
- **Detection**: Reconciler reads existing row, sees `status=final`, refuses to demote.
- **Action**: None — this is the designed behavior. Log a structured warning at `info` level for the audit trail.

## ERR_TXP_002 — transcript_missing_after_threshold

- **Source**: Reconciler / fallback poller
- **Cause**: A `call.ended` was received N hours ago but no `call.transcript.partial` or `call.transcript.completed` has followed.
- **Detection**: Poller compares `call.ended` inbox rows to `call.transcript.*` rows; finds an unmatched `call.ended` past `missing_transcript_threshold_hours` (default 4h).
- **Action**: Poller fetches the transcript directly from `GET /v4/conversations/{id}/transcript`. If the API returns 200, synthesize a `call.transcript.completed` inbox row tagged `source=poller`. If the API returns 404 (transcript never produced), mark the call's transcript status `failed` and emit a metric.

## ERR_TXP_003 — language_undetermined_short_transcript

- **Source**: Language detector
- **Cause**: Transcript body is shorter than `min_chars_for_detection` (default 20 chars). `langdetect` cannot produce a reliable signal.
- **Detection**: `detect_transcript_language()` returns `("und", 0.0)`.
- **Action**: Route the record to `queue:rag.transcripts.review` for human-review handling. Do not feed to an LLM.

## ERR_TXP_004 — presidio_unavailable_regex_only

- **Source**: Redactor
- **Cause**: `presidio_analyzer` import failed (missing package, missing spaCy model) or initialization threw.
- **Detection**: Try-import guard at module load; per-call sanity check on the analyzer engine.
- **Action**: Run with the regex layer only. Emit a structured warning **per transcript** so the operator sees the degradation in dashboards. Page on-call if the warning persists for >1h (indicates a deploy regression, not a transient).

## ERR_TXP_005 — queue_write_failed_retrying

- **Source**: Queue writer
- **Cause**: Outbound queue rejected the write (Redis disconnected, SQS throttled, SQLite locked).
- **Detection**: Queue client raised; processor catches.
- **Action**: Increment `attempt_count`, set `next_attempt_at = now + min(2^attempts, cap_seconds)`. The processor's next pass will retry. No data loss — record stays in the inbox.

## ERR_TXP_006 — oversize_single_segment_chunk

- **Source**: Chunker
- **Cause**: A single transcript segment is larger than `target_tokens` (1500 by default). The chunker refuses to split a speaker turn, so emits a one-segment oversize chunk.
- **Detection**: After processing a segment, the chunk's `token_count > target_tokens` AND there is only one segment in the chunk.
- **Action**: Allowed by default (`allow_oversize_single_segment_chunks=true`). Emit an `info` log with the transcript_id and segment duration. If oversize chunks become common (>1% of chunks), revisit Podium's segment splitting upstream.

## ERR_TXP_007 — dead_letter_row_inserted

- **Source**: Processor
- **Cause**: A record's `attempt_count` exceeded `max_attempts` (default 12). The processor refuses to retry further.
- **Detection**: Processor checks `attempt_count` before scheduling next retry; on threshold, inserts into `inbox_deadletter` and deletes from `inbox`.
- **Action**: Page on-call immediately. The alert rule on `inbox_deadletter` count > 0 for > 1h fires automatically. Inspect `last_error` column to diagnose; replay manually after fix via `INSERT INTO inbox SELECT * FROM inbox_deadletter WHERE id = ?`.

## ERR_TXP_008 — signature_verification_failed

- **Source**: Webhook handler
- **Cause**: `verify_webhook()` (from `podium-webhook-reliability`) returned false. Either the request is forged or the webhook secret in this skill's config does not match the secret registered with Podium.
- **Detection**: Handler returns 401 before inbox insert.
- **Action**: Return 401 to caller. Log the source IP and timestamp. If verified failures spike, audit the webhook secret config and verify it matches the value in the Podium developer console.

## ERR_TXP_009 — inbox_write_failed_returning_5xx

- **Source**: Webhook handler
- **Cause**: SQLite write failed (disk full, permission error, database corruption).
- **Detection**: Handler catches the exception from `inbox.insert()`.
- **Action**: Return 5xx to Podium so it retries the webhook. Page on-call — this is an infrastructure failure that data integrity depends on. Do **not** return 200 with a dropped event.

## ERR_TXP_010 — malformed_transcript_payload

- **Source**: Reconciler / chunker
- **Cause**: A transcript event has a payload missing required fields (`transcript_id`, `segments[]`, or per-segment `speaker_role`).
- **Detection**: JSON parse + schema check at the top of `build_outbound_record()`.
- **Action**: Move the row directly to `inbox_deadletter` (do not retry — retries will not fix a schema bug). Page on-call with the row id and the missing fields list. Either Podium changed the payload shape or an upstream tool corrupted the event; investigate before manual replay.
