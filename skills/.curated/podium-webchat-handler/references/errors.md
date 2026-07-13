# Errors — podium-webchat-handler

Lookup table for `ERR_WEBCHAT_*` codes raised by the library and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_WEBCHAT_001 — invalid_phone_format

- **HTTP**: 400 from `phonenumbers.parse` failure or `is_valid_number()` returning False
- **Cause**: The raw phone the widget submitted cannot be parsed for the supplied `default_country`, or parses to an invalid number for that region.
- **Detection**: `normalize_phone()` raises `PhoneValidationError`.
- **Action**: Refuse the webchat submission at the widget. Surface the error inline so the customer can correct. Offer a `+`-prefixed international fallback. Do NOT silently default to another country.

## ERR_WEBCHAT_002 — missing_location_uid

- **HTTP**: 400 raised by `validate_location()`
- **Cause**: The webchat event arrived without a `location_uid` field, or the field was empty.
- **Detection**: `validate_location(None)` raises `WebchatError`.
- **Action**: Reject the request and surface the config error to the widget operator. The widget embed snippet for this store is misconfigured — every per-location embed must carry its own `location_uid`. There is NO default fallback by design (see SKILL.md production failure #5).

## ERR_WEBCHAT_003 — unknown_location_uid

- **HTTP**: 400 raised by `validate_location()`
- **Cause**: The `location_uid` supplied does not match any entry loaded from `/v4/locations`.
- **Detection**: `location_uid not in VALID_LOCATION_UIDS`.
- **Action**: First, force a `load_locations()` refresh — the location may have been added since the last cache load. If the slug is still unknown after refresh, the widget is misconfigured or the slug is from a different Podium org. Page the integration owner.

## ERR_WEBCHAT_004 — contact_upsert_conflict_unresolved

- **HTTP**: 409 followed by an empty refetch
- **Cause**: A racing creator returned 409 on the create call, but the immediate refetch found no record with that phone. This is a rare ordering window where the racing writer has not yet committed.
- **Detection**: `upsert_contact_by_phone()` exhausted `conflict_refetch_max_attempts` (default 3) without finding the record.
- **Action**: Retry the upsert after a short delay. If the condition persists, investigate the racing writer (typically another instance of the handler). Long-term: enforce a database-level unique index on `phone_e164` so the racing path is serialized at the DB layer.

## ERR_WEBCHAT_005 — attachment_too_large

- **HTTP**: 413 (client-side rejected before upload starts; server-side double-check)
- **Cause**: Attachment exceeds Podium's 25 MiB limit.
- **Detection**: `validate_attachment_size(size_bytes)` raises `AttachmentTooLargeError`, OR the server-side `Content-Length` check returns 413.
- **Action**: Surface the size limit to the customer in the widget. Suggest compression or smaller attachments. Do NOT forward to Podium — the upload will fail server-side and waste both your egress and the customer's time.

## ERR_WEBCHAT_006 — session_idle_close

- **HTTP**: N/A (raised by the session scanner)
- **Cause**: A webchat session has been idle for ≥ `session.idle_close_seconds` (default 28 min). Close it cleanly before Podium expires it unilaterally.
- **Detection**: `scan_sessions()` finds a session with `status() == "close"`.
- **Action**: Persist `partial_state`, call `POST /v4/conversations/{uid}/close`, drop the session from the active map. On the next message from the same `(phone_e164, location_uid)`, hydrate the persisted `partial_state` so the customer is not asked to restart.

## ERR_WEBCHAT_007 — session_idle_warn

- **HTTP**: N/A (informational)
- **Cause**: A webchat session has been idle for ≥ `session.idle_warn_seconds` (default 20 min) but less than the close threshold.
- **Detection**: `scan_sessions()` finds a session with `status() == "warn"`.
- **Action**: Send a keepalive prompt to the customer ("Still there? Type anything to keep the chat open."). Do NOT close the session yet — the customer may resume.

## ERR_WEBCHAT_008 — optout_keyword_received

- **HTTP**: N/A (informational)
- **Cause**: An inbound message body matched one of the configured opt-out keywords.
- **Detection**: `text.strip().upper() in OPTOUT_KEYWORDS`.
- **Action**: Write the opt-out to the unified store keyed on `phone_e164`. Mirror to Podium via `PATCH /v4/contacts/{uid}`. Do NOT send any reply. Acknowledge silently — the opt-out itself is the receipt.

## ERR_WEBCHAT_009 — optout_blocked_outbound

- **HTTP**: N/A (raised before any outbound API call)
- **Cause**: An outbound message attempt was blocked because the destination phone is recorded as opted-out.
- **Detection**: `check_optout(phone_e164)` returns True before the outbound call.
- **Action**: Drop the outbound attempt. Log to the compliance channel. This is the correct path; the alert exists so a high rate of these alerts can surface a bug in upstream code that is still attempting outbound to opted-out contacts.

## ERR_WEBCHAT_010 — optout_store_unreachable

- **HTTP**: N/A (raised by the opt-out store client)
- **Cause**: The opt-out store (Postgres / Redis / DynamoDB) is unreachable or returning errors.
- **Detection**: Store client raises a connection or timeout error.
- **Action**: With `optout.fail_mode: closed` (default), block ALL outbound until the store is reachable again. The availability cost is intentional; the compliance cost of sending to an opted-out contact dominates. Page on-call.

## ERR_WEBCHAT_011 — optout_attempt_after_block_detected

- **HTTP**: N/A (raised by the audit layer)
- **Cause**: A downstream system bypassed `check_optout()` and attempted to send to an opted-out phone — the audit caught it post-fact.
- **Detection**: Audit log shows outbound traffic to a phone present in the opt-out store.
- **Action**: Page compliance immediately. This is a code bug, not a transient issue. The bypassing code path must be fixed before the integration resumes outbound.

## ERR_WEBCHAT_012 — location_routing_rejection_burst

- **HTTP**: N/A (raised when rejection rate exceeds threshold)
- **Cause**: More than N missing-or-unknown `location_uid` rejections in M minutes — typically a widget config that was deployed without `location_uid`.
- **Detection**: Rate counter on `ERR_WEBCHAT_002` + `ERR_WEBCHAT_003`.
- **Action**: Page the integration owner. The store's widget embed needs a fix and is dropping every incoming chat until then.

## ERR_WEBCHAT_013 — partial_state_hydration_failure

- **HTTP**: N/A (raised on the resume path)
- **Cause**: A new message arrived from a `(phone, location)` pair that had a previously-persisted `partial_state`, but the hydration read failed.
- **Detection**: `hydrate_partial_state()` raises `OSError` or backend error.
- **Action**: Continue with fresh state — the customer experiences the same "context lost" failure mode the skill is designed to prevent, but the message itself still goes through. Log to ops-warnings; if the rate exceeds 1/hour, investigate the persistence path.

## ERR_WEBCHAT_014 — locations_refresh_stale

- **HTTP**: N/A (raised when refresh has not completed in > 2x interval)
- **Cause**: The periodic `/v4/locations` refresh has not completed in over 2x its configured interval. The valid-location set may be stale; new stores cannot be routed to.
- **Detection**: `locations_last_refreshed_at` older than `refresh_interval_seconds * 2`.
- **Action**: Force a refresh via the operator CLI. If the refresh is failing, check `podium-auth` for scope drift (`locations.read` may have been removed) or `podium-rate-limit-survival` for throttling.
