# Errors — podium-auth

Lookup table for `ERR_AUTH_*` codes raised by the library and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_AUTH_001 — invalid_grant

- **HTTP**: 401 from `POST /oauth/token`
- **Cause**: The refresh token is expired (>90 days unused) or has been revoked.
- **Detection**: `_refresh()` returns 401 with body `{"error": "invalid_grant"}`.
- **Action**: Re-authorize the Podium OAuth app via the user-facing flow. No automated recovery is possible — a user must click through `/oauth/authorize` again. Page on-call to coordinate with the customer.

## ERR_AUTH_002 — invalid_client

- **HTTP**: 400 from `POST /oauth/token`
- **Cause**: The `client_id` or `client_secret` does not match a registered OAuth app.
- **Detection**: `_refresh()` returns 400 with body `{"error": "invalid_client"}`.
- **Action**: Verify credentials in the Podium developer console. If a rotation is in progress, confirm the new secret has been deployed and the cache has been signaled to reload.

## ERR_AUTH_003 — invalid_token

- **HTTP**: 401 from any `api.podium.com` endpoint
- **Cause**: Access token is malformed, expired, or revoked.
- **Detection**: Caller receives 401 on a data-plane call.
- **Action**: Force a refresh via `auth._refresh()`. If the refresh succeeds and the data call still 401s, the access token was revoked server-side — re-authorize.

## ERR_AUTH_004 — insufficient_scope

- **HTTP**: 403 from any `api.podium.com` endpoint
- **Cause**: The OAuth token does not have the scope required by the endpoint.
- **Detection**: Caller receives 403 with a `WWW-Authenticate: Bearer scope=...` header.
- **Action**: Run `scope_audit.py` to compare granted vs required. If a recent admin re-grant reduced scopes, the admin must re-grant the missing scopes in the Podium org settings.

## ERR_AUTH_005 — rate_limited_auth_endpoint

- **HTTP**: 429 from `POST /oauth/token`
- **Cause**: Too many refresh attempts in a short window (typically caused by a thundering-herd refresh storm bypassing the single-flight lock).
- **Detection**: `_refresh()` returns 429.
- **Action**: Honor `Retry-After`. Audit the integration for code paths that call `_refresh()` directly instead of going through `get_token()`. The single-flight lock should make this unreachable.

## ERR_AUTH_006 — refresh_token_persistence_failure

- **HTTP**: N/A (local I/O error)
- **Cause**: Atomic write of the new refresh token to the secret store failed (disk full, permissions, secret-store API outage).
- **Detection**: `_persist_refresh_token()` raises `OSError` or backend-specific exception.
- **Action**: Critical — the system holds a new refresh token in memory that has not been persisted. Do NOT crash the process; retry the persist with exponential backoff. If persistence keeps failing after `max_attempts`, raise and page on-call so the operator can manually rescue the in-memory refresh token.

## ERR_AUTH_007 — scope_drift_detected

- **HTTP**: N/A (raised by `validate_scopes()`)
- **Cause**: Refresh succeeded but the returned `scope` field is missing one or more required scopes.
- **Detection**: `validate_scopes(body)` raises `PodiumScopeError(missing=[...])`.
- **Action**: Page on-call. The Podium org admin must re-grant the OAuth app with the full required scope set.

## ERR_AUTH_008 — decay_warn

- **HTTP**: N/A (logged by `check_decay`)
- **Cause**: Refresh-token `last_used_at` is older than 60 days. The token will hard-fail at 90 days.
- **Detection**: Background decay monitor or pre-refresh check.
- **Action**: No immediate action. Log to the ops-warning channel. If the warn persists for >7 days, schedule a forced refresh.

## ERR_AUTH_009 — decay_page

- **HTTP**: N/A (paged by `check_decay`)
- **Cause**: Refresh-token `last_used_at` is older than 75 days.
- **Detection**: Background decay monitor.
- **Action**: Page on-call. Either trigger a forced refresh (if the integration is operational and just idle) or initiate user re-authorization (if the integration is paused/decommissioned).

## ERR_AUTH_010 — decay_hard_fail

- **HTTP**: N/A (raised by `check_decay`)
- **Cause**: Refresh-token `last_used_at` is older than 85 days. Refresh attempts beyond this point will eat into the 90-day ceiling with no margin.
- **Detection**: Raised on the next `get_token()` call.
- **Action**: Initiate user re-authorization immediately. The integration is non-functional until a new refresh token is obtained.

## ERR_AUTH_011 — unknown_org_slug

- **HTTP**: N/A (raised by `PodiumOrgRouter`)
- **Cause**: A consumer requested a token for an org slug not present in the credentials map.
- **Detection**: `router.get_token("acme-rv")` raises `KeyError`.
- **Action**: Verify the slug against the canonical org list. If the org was recently onboarded, confirm its credentials were added to the credentials map and the router was reloaded.

## ERR_AUTH_012 — credential_leak_detected

- **HTTP**: N/A (raised by `scripts/scope_audit.py` or a pre-commit hook)
- **Cause**: A grep audit found a string matching the Podium client-secret or refresh-token format in tracked source files.
- **Detection**: `grep -rnE "podium.*(client_secret|refresh_token)\s*=\s*['\"]"` returns non-empty.
- **Action**: Treat as a security incident. Rotate the leaked credential **immediately** (within minutes — Podium client secrets do not auto-expire). After rotation completes, audit git history (`git log -p`) for the leak window and assess data-access scope.

## ERR_AUTH_013 — health_check_failed_during_rotation

- **HTTP**: N/A (raised by `rotate_secret.py`)
- **Cause**: Post-rotation `GET /v4/me` did not return 200 with the new credential.
- **Detection**: `verify_credential(new_token)` returns false.
- **Action**: Abort the rotation. **Do not revoke the old secret.** Restore the cache to use the old secret, investigate the new-secret configuration, and retry rotation only after the root cause is understood.

## ERR_AUTH_014 — concurrent_rotation_detected

- **HTTP**: N/A (raised by `rotate_secret.py`)
- **Cause**: Two operators attempted secret rotation simultaneously; the second sees a `rotation_in_progress` marker in the secret store.
- **Detection**: `rotate_secret.py` finds an unstale lock marker.
- **Action**: Confirm via team channel that another rotation is genuinely in progress. If the marker is stale (>30 minutes old, originating process is dead), delete the marker and retry. Never force-rotate around a live lock.
