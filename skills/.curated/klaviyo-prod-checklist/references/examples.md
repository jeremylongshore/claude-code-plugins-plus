# Klaviyo Production Checklist — Worked Examples

Concrete runs of the go-live workflow. Each shows the command, the expected
output, and how to read the result.

## Example 1 — Green pre-flight (safe to deploy)

```bash
$ export KLAVIYO_PRIVATE_KEY=pk_live_xxxxxxxx
$ ./scripts/preflight-klaviyo.sh
=== Klaviyo Production Pre-Flight ===
Klaviyo Status Page: All Systems Operational
API Auth: HTTP 200
Rate Limit: ratelimit-remaining: 690
SDK Version: 16.0.0
=== Pre-flight complete ===
```

All four gates pass — status page clean, auth returns `200`, rate-limit
headroom is healthy, and the SDK version is pinned. Proceed with the deploy.

## Example 2 — Failed auth (blocked)

```bash
$ ./scripts/preflight-klaviyo.sh
=== Klaviyo Production Pre-Flight ===
Klaviyo Status Page: All Systems Operational
API Auth: HTTP 403
FAIL: API auth returned 403
```

The script exits non-zero at gate 2. A `403` means the key is revoked or lacks
the required scopes — this is a **P1**. Rotate/repair the key before retrying;
do not deploy.

## Example 3 — Reading the health endpoint after deploy

```bash
$ curl -s localhost:3000/health | python3 -m json.tool
{
    "status": "healthy",
    "services": {
        "klaviyo": {
            "status": "healthy",
            "latencyMs": 142,
            "accountId": "AbC123"
        }
    },
    "timestamp": "2026-07-17T14:03:11.482Z"
}
```

A `healthy` status with sub-500ms latency confirms the live integration is
reachable. A `degraded` status (HTTP 429 from Klaviyo) or `down` status returns
`503` and should trip the alert thresholds in `SKILL.md`.

## Example 4 — Instant rollback via feature flag

```bash
# Klaviyo 5xx spiking post-deploy — cut traffic to the integration immediately
$ your-platform env:set KLAVIYO_ENABLED=false
# App degrades gracefully; no redeploy needed. Investigate, then re-enable.
```

Prefer the feature flag over a git revert when you need to stop the bleeding in
seconds. Fall back to `git revert HEAD` or `kubectl rollout undo` (see
`references/implementation.md`) only when the flag path is unavailable.
