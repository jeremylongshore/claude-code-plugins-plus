# Intercom Pre-Flight and Rollback — Runnable Examples

Copy-paste scripts for the go-live gate and the emergency rollback path.

## Pre-flight verification script

Run this immediately before flipping the production feature flag. It fails fast
(`exit 1`) on an auth failure, so it is safe to chain into a deploy pipeline gate.

```bash
#!/bin/bash
set -euo pipefail

echo "=== Intercom Production Pre-Flight ==="

# 1. Auth check
echo -n "Auth: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me)
[ "$STATUS" = "200" ] && echo "PASS" || { echo "FAIL ($STATUS)"; exit 1; }

# 2. Rate limit headroom
echo -n "Rate limit remaining: "
REMAINING=$(curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i x-ratelimit-remaining | awk '{print $2}')
echo "$REMAINING"

# 3. Intercom platform status
echo -n "Intercom status: "
curl -s https://status.intercom.com/api/v2/status.json | jq -r '.status.indicator'

# 4. Webhook endpoint reachable (if configured)
if [ -n "${WEBHOOK_URL:-}" ]; then
  echo -n "Webhook endpoint: "
  WH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$WEBHOOK_URL")
  echo "$WH_STATUS"
fi

echo "=== Pre-flight complete ==="
```

Expected healthy output:

```
=== Intercom Production Pre-Flight ===
Auth: PASS
Rate limit remaining: 9987
Intercom status: none
Webhook endpoint: 200
=== Pre-flight complete ===
```

An `Intercom status:` value of `none` means no active incident; `minor`,
`major`, or `critical` indicate a platform-side degradation — hold the launch.

## Rollback procedure

Execute top-to-bottom when a launched integration is failing in production. The
feature flag is flipped first so no new traffic reaches Intercom while the
deployment rolls back.

```bash
# 1. Disable Intercom integration via feature flag
curl -X PATCH https://your-config-service/flags/intercom_enabled \
  -d '{"value": false}'

# 2. If using k8s, rollback deployment
kubectl rollout undo deployment/intercom-service
kubectl rollout status deployment/intercom-service

# 3. Verify rollback
curl -s https://your-app.com/health | jq '.services.intercom'

# 4. Disable webhooks in Intercom Developer Hub
# (prevents queued webhook deliveries to unhealthy endpoint)
```
