# Errors — podium-multi-location-router

Lookup table for `ERR_LOC_*` codes raised by the router library and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_LOC_001 — unknown_location_uid

- **HTTP**: N/A (raised by `LocationRouter.get_client()`)
- **Cause**: The caller passed a `location_uid` that is not in the credentials map.
- **Detection**: `router.get_client("not-in-map")` raises `UnknownLocationError`.
- **Action**: Verify the UID against the canonical location list. If the location was recently onboarded, confirm `onboard_location.py` completed successfully and the router was reloaded. There is no fallback path by design — a typo'd UID must surface, not silently route to a default.

## ERR_LOC_002 — location_not_in_scope

- **HTTP**: 403 from `GET /v4/locations` pre-flight (raised as `LocationNotInScopeError`)
- **Cause**: The token for this credential record does not own the requested `location_uid`. Most commonly: the credentials map has a wrong-org pairing — the `client_id`/`refresh_token` is for org A but the `location_uid` belongs to org B.
- **Detection**: `ensure_location_verified()` calls `GET /v4/locations` and the returned set does not contain the requested UID.
- **Action**: Run `verify_location.py --location-uid <uid> --credentials-file <map>` to confirm. If genuinely wrong-org, fix the credentials map entry to point at the correct OAuth app. **Do not** add a fallback path — this error means the routing layer just prevented a silent wrong-org write.

## ERR_LOC_003 — verification_endpoint_unreachable

- **HTTP**: 5xx / timeout from `GET /v4/locations`
- **Cause**: Podium-side outage or network failure at pre-flight time.
- **Detection**: `ensure_location_verified()` receives a non-200 response and the location is not in the verified cache.
- **Action**: On first occurrence, retry with exponential backoff (max 4 attempts). If Podium is broadly down, the integration enters a degraded mode where only previously-verified locations (still within TTL) can write; new locations or stale verifications return `ERR_LOC_003` until the endpoint recovers.

## ERR_LOC_004 — audit_log_write_failure

- **HTTP**: N/A (local I/O error)
- **Cause**: The audit log append failed (disk full, permissions error, log path unwritable).
- **Detection**: `emit_audit()` raises `OSError`.
- **Action**: Critical — an unaudited call is not an acceptable degradation mode. The library configuration `fail_call_on_audit_failure: true` causes the API call itself to fail. On-call investigates disk space, log rotation, and permissions on the audit-log directory. **Never** patch around this by silencing the audit write; the compliance trail is the entire point of the skill.

## ERR_LOC_005 — onboarding_partial_failure

- **HTTP**: N/A (raised by `onboard_locations()`)
- **Cause**: One or more locations in a bulk-onboarding operation failed verification or credential persistence.
- **Detection**: `OnboardingResult` list contains at least one `status == "failed"` entry.
- **Action**: Inspect the per-location error in the result list. Re-run `onboard_location.py` with the same input — already-onboarded locations are detected and skipped. The atomic-per-location invariant guarantees no dangling half-records on the retry.

## ERR_LOC_006 — credential_persistence_failure

- **HTTP**: N/A (local I/O error)
- **Cause**: Atomic write of a new credential entry to the credentials map failed mid-onboarding.
- **Detection**: `_persist_credential()` raises during onboarding.
- **Action**: The orchestrator rolls back the in-memory map entry to maintain the atomic invariant. Investigate disk space and permissions on the credentials-map directory. Re-run onboarding; idempotent on retry.

## ERR_LOC_007 — location_rate_limit_exceeded

- **HTTP**: 429 from Podium (raised as `LocationRateLimitExceeded`)
- **Cause**: The per-location token bucket cannot acquire within the configured timeout. Either the location is in genuine burst traffic or the bucket is sized too small.
- **Detection**: `bucket.acquire()` times out, OR Podium returns 429 despite a bucket acquire (rare; indicates org-level quota exceeded).
- **Action**: Caller honors `Retry-After` and retries. If the location regularly hits this, tune `default_capacity` / `default_refill_per_second` in `config/settings.yaml` or set a per-location override in the credentials map. **Do not** share a bucket across locations as a workaround — that re-introduces ERR_LOC_011.

## ERR_LOC_008 — credentials_map_load_failure

- **HTTP**: N/A (raised at router init)
- **Cause**: The credentials map file is missing, unreadable, or malformed.
- **Detection**: `LocationRouter.from_credentials_file()` raises `OSError` or `json.JSONDecodeError`.
- **Action**: Verify the map path, file permissions (0600 owner-only is standard), and JSON / SOPS YAML validity. The router refuses to start with a bad map rather than partially initialize — operate at full-router-or-no-router granularity.

## ERR_LOC_009 — duplicate_location_uid_in_map

- **HTTP**: N/A (raised at router init)
- **Cause**: The credentials map contains two entries with the same `location_uid`.
- **Detection**: Map parser sees a duplicate key.
- **Action**: Deduplicate the map. The two entries probably represent a stale credential alongside a fresh one — keep the entry matching the active OAuth app and delete the stale one. Re-run `verify_location.py` against the kept entry.

## ERR_LOC_010 — location_deleted_on_podium_side

- **HTTP**: 404 from `GET /v4/contacts` (or other data-plane endpoint)
- **Cause**: A previously-verified `location_uid` no longer exists on Podium — typically because an operator deleted the location in the Podium console.
- **Detection**: Pre-flight `ensure_location_verified()` will catch this on the next TTL expiry. Until then, calls return 404.
- **Action**: Remove the entry from the credentials map and alert the operator who owns that location. The audit log still contains the historical calls for compliance purposes — the credentials-map removal is a forward-looking change only.

## ERR_LOC_011 — shared_bucket_starvation_detected

- **HTTP**: N/A (operational anti-pattern, not a runtime error)
- **Cause**: A bucket was incorrectly shared across multiple `location_uid` keys. One location's burst starves the others.
- **Detection**: Audit log shows clustered 429s across multiple locations within the same minute, traceable to a single bucket-acquire call site.
- **Action**: Architectural fix — each `location_uid` must have its own `TokenBucket` instance. Audit the `LocationRouter.bucket_for()` implementation to confirm one-to-one keying. If a per-customer integration shares buckets to "save memory," that is a security regression masquerading as optimization; reject it.

## ERR_LOC_012 — audit_log_schema_violation

- **HTTP**: N/A (raised at audit-log write time)
- **Cause**: A code change produced an audit-log record missing one of the 8 required fields (`ts, location_uid, org_slug, endpoint, method, status, request_id, latency_ms`).
- **Detection**: The library validates against the schema before write; missing field raises.
- **Action**: This is a programming error in the caller of `emit_audit()`. The compliance contract is that every audit line has every field. Fix the calling code; do not relax the schema check.
