# Errors — podium-webhook-reliability

Lookup table for `ERR_WHK_*` codes raised by the receiver and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_WHK_001 — missing_signature_header

- **HTTP**: 401 from receiver
- **Cause**: Inbound POST has no `X-Podium-Signature` header (or whatever the configured header name is).
- **Detection**: `receive()` checks `request.headers` and the header is absent.
- **Action**: Confirm the request actually originated from Podium. If it did, audit Podium-side webhook configuration. If it did not, the URL is being probed — confirm fail-closed and audit access logs.

## ERR_WHK_002 — signature_mismatch

- **HTTP**: 401 from receiver
- **Cause**: HMAC-SHA256 over the raw body with the signing secret does not match the `v1=` value in the header.
- **Detection**: `hmac.compare_digest(computed, received)` returns False.
- **Action**: First, confirm the body was read raw and not re-encoded by middleware (the most common cause of false-positive mismatches). Second, confirm the signing secret is the current one and not a rotated-out version. If neither — treat as a probe and log only IP + timestamp.

## ERR_WHK_003 — replay_window_exceeded

- **HTTP**: 401 from receiver
- **Cause**: The `t=<unix_ts>` value in the signature header is more than `window_seconds` (default 300) from now in either direction.
- **Detection**: `within_replay_window(ts)` returns False after signature verify passes.
- **Action**: If receiver clock skew is the cause (host's NTP is drifted), fix the clock and the events resume. If a legitimate Podium delivery is queued internally for >5min, raise the window or fix the Podium-side queue. If neither — treat as a captured-and-replayed event, do not log the body, audit access logs.

## ERR_WHK_004 — body_not_parseable

- **HTTP**: 400 from receiver
- **Cause**: Signature verified but `json.loads(raw)` raised — body is not valid JSON.
- **Detection**: `json.JSONDecodeError` after signature pass.
- **Action**: Confirm Podium is sending JSON (vs form-encoded or other). This should be impossible for a real Podium delivery — investigate as a Podium-side bug.

## ERR_WHK_005 — duplicate_event

- **HTTP**: 200 from receiver with `{"status": "duplicate"}`
- **Cause**: `claim_event(event_id)` returned False — the event_id is already in the dedup cache.
- **Detection**: Redis `SET NX EX 86400` returned 0 / Python `False`.
- **Action**: Expected behavior on a Podium retry. No action required. If duplicate count is unexpectedly high (>5% of requests), investigate Podium-side — receiver may be returning 5xx more often than expected, triggering more retries.

## ERR_WHK_006 — dedup_backend_unavailable

- **HTTP**: 503 from receiver
- **Cause**: Redis (or configured dedup backend) is unreachable; receiver fails closed.
- **Detection**: Redis client raises `ConnectionError` or times out.
- **Action**: This is a sidecar outage, not a Podium outage. Restore Redis. Until then, every webhook gets retried by Podium — the 24h retry window is forgiving but not infinite. If Redis cannot be restored quickly, do NOT switch to `log_and_continue` — replay-from-Podium is safer than duplicate processing.

## ERR_WHK_007 — dispatch_handler_raised

- **HTTP**: 500 from receiver
- **Cause**: The application handler raised an exception during event processing.
- **Detection**: `try: dispatch(event)` caught an exception. The exception is logged and the event is persisted to the DLQ before the 500 is returned.
- **Action**: Investigate the exception in logs. Fix the handler bug. Drain DLQ via `dlq_replay.py` once the fix is deployed. The original event is also being retried by Podium — but the DLQ entry is the authoritative recovery path because it carries the original signed payload independent of Podium's retry clock.

## ERR_WHK_008 — dlq_persist_failed

- **HTTP**: 500 from receiver (paged)
- **Cause**: Handler raised AND the DLQ persist also failed. The event is now at risk of loss.
- **Detection**: `dlq_persist()` raised after `dispatch()` raised.
- **Action**: **Critical, page on-call.** Podium will retry the event, but the DLQ path that exists for handler-bug recoveries is now broken. Investigate DLQ backend (Redis list health, SQLite file permissions, disk full). Until the DLQ is healthy, every handler exception risks event loss after Podium gives up retrying.

## ERR_WHK_009 — out_of_order_precondition_missing

- **HTTP**: 200 from receiver (deferred to DLQ for replay)
- **Cause**: A causally-dependent event arrived before its precondition (e.g. `conversation.deleted` for a conversation that does not yet exist locally).
- **Detection**: The handler's precondition check returned False; the event was persisted to the DLQ with `reason: out_of_order_*`.
- **Action**: Expected when batches arrive out of order. The replay path (`dlq_replay.py`) will re-attempt these on the next drain — by then the precondition (the `conversation.created` event) will have landed and the deferred event will succeed.

## ERR_WHK_010 — dlq_backlog_overflow

- **HTTP**: 503 from receiver (paged)
- **Cause**: DLQ has more than `max_backlog` entries (default 100,000). Receiver refuses new events to prevent unbounded storage growth.
- **Detection**: DLQ size probe at request entry exceeded the cap.
- **Action**: Investigate the root cause of the backlog — almost always a persistent handler bug. Fix the handler, drain the DLQ via `dlq_replay.py`, then receiver resumes accepting events. Do NOT just raise the cap.

## ERR_WHK_011 — body_size_exceeded

- **HTTP**: 413 from receiver
- **Cause**: Inbound body is larger than `max_body_bytes` (default 512 KiB).
- **Detection**: FastAPI / uvicorn enforces the cap before signature verify.
- **Action**: Legitimate Podium events are small (~few KB). A 512+ KiB POST is either a Podium-side bug, a misconfigured proxy doubling the body, or a probe. Investigate logs; treat as a probe if not Podium-origin.

## ERR_WHK_012 — signature_format_invalid

- **HTTP**: 401 from receiver
- **Cause**: The signature header value did not parse into the expected `t=<...>,v1=<...>` key=value pairs.
- **Detection**: `parts = dict(p.split("=", 1) for p in header.split(","))` produced a dict missing `t` or `v1`.
- **Action**: Confirm Podium has not changed the signature header format. If they have, update `signature.format` in `config/settings.yaml` and the parser in `verify_signature()`. If the format is unchanged, treat as a probe.
