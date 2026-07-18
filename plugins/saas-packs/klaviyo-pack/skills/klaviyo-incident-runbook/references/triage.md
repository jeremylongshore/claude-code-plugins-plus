# Triage and Decision Tree

The full triage script and decision tree for a Klaviyo incident. Run the triage
script first during any incident, then walk the decision tree to classify the
failure and route to the right remediation.

## Quick Triage (Run Immediately)

```bash
#!/bin/bash
# klaviyo-triage.sh -- run this first during any incident

echo "=== Klaviyo Quick Triage ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Is Klaviyo itself down?
echo ""
echo "--- Klaviyo Status Page ---"
curl -s "https://status.klaviyo.com/api/v2/status.json" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"][\"description\"]}')" \
  || echo "Could not reach status page"

# 2. Can we authenticate?
echo ""
echo "--- API Auth Check ---"
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/klaviyo-triage.json \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/" 2>/dev/null)
echo "Auth response: HTTP $HTTP_CODE"

# 3. Rate limit status
echo ""
echo "--- Rate Limit Headers ---"
curl -s -I \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
  | grep -iE "ratelimit|retry-after" || echo "No rate limit headers returned"

# 4. Our app health
echo ""
echo "--- Application Health ---"
curl -s "http://localhost:3000/health" 2>/dev/null \
  | python3 -m json.tool 2>/dev/null || echo "App health check unavailable"
```

The `revision: 2024-10-15` header pins the Klaviyo API to a dated, stable
version — Klaviyo requires this header on every request, and keeping it fixed
across an incident guarantees a consistent contract while you debug.

## Decision Tree

```
Is Klaviyo API returning errors?
├── YES
│   ├── status.klaviyo.com shows incident?
│   │   ├── YES → Klaviyo-side outage
│   │   │   → Enable fallback mode
│   │   │   → Monitor status page for resolution
│   │   │   → Communicate to stakeholders
│   │   └── NO → Our integration issue
│   │       ├── 401/403? → API key problem (see below)
│   │       ├── 429? → Rate limit hit (see below)
│   │       ├── 400? → Payload validation error
│   │       └── 5xx? → Likely intermittent, retry with backoff
│   └── What status code?
│       ├── 401 → Key revoked/rotated → Verify & rotate
│       ├── 403 → Missing scope → Check API key scopes
│       ├── 429 → Rate limited → Reduce concurrency
│       └── 5xx → Server error → Retry, check status page
└── NO
    ├── Is our app healthy?
    │   ├── YES → Resolved or intermittent → Monitor
    │   └── NO → Our infrastructure → Check pods, memory, network
    └── Are webhooks arriving?
        ├── YES → Partial issue → Check specific endpoint
        └── NO → Webhook endpoint down → Check route, certificate
```
