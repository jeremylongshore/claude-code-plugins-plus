# Triage — Full Diagnostic Script & Decision Tree

Deep reference for the first phase of an Intercom incident. SKILL.md carries the
essential first command; this file carries the full copy-paste triage script and
the complete branch-by-branch decision tree.

## Quick Triage (Copy-Paste)

```bash
#!/bin/bash
echo "=== Intercom Incident Triage ==="

# 1. Is Intercom's API responding?
echo -n "1. API reachable: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me
echo ""

# 2. Is there a platform-wide incident?
echo -n "2. Intercom status: "
curl -s https://status.intercom.com/api/v2/status.json | jq -r '.status.description'

# 3. Active incidents on Intercom's side?
echo -n "3. Active incidents: "
curl -s https://status.intercom.com/api/v2/incidents/unresolved.json | jq '.incidents | length'

# 4. Rate limit status
echo -n "4. Rate limit remaining: "
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i x-ratelimit-remaining | awk '{print $2}'

# 5. Our health check
echo -n "5. Our integration health: "
curl -s https://your-app.com/health | jq '.services.intercom.status' 2>/dev/null || echo "UNKNOWN"
```

## Decision Tree

```
API returning errors?
├── YES ──▶ Check status.intercom.com
│           ├── Incident reported ──▶ Intercom's problem
│           │   → Enable graceful degradation
│           │   → Monitor for resolution
│           │   → No action needed on our side
│           └── No incident ──▶ Our integration issue
│               ├── 401 → Token expired/revoked → Rotate token
│               ├── 403 → Scope missing → Add OAuth scope
│               ├── 429 → Rate limited → Enable queue/backoff
│               └── 5xx → Server error → Retry with backoff
└── NO ──▶ Is our service healthy?
           ├── YES → Resolved or intermittent → Monitor
           └── NO → Our infrastructure issue
               → Check pods, memory, network, DNS
```
