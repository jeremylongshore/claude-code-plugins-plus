# Shopify Incident Triage Script

Quick triage script to run in the first 5 minutes of an incident. Checks Shopify status, API connectivity, REST rate limits, and GraphQL throttle state.

```bash
#!/bin/bash
echo "=== SHOPIFY INCIDENT TRIAGE ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Is Shopify itself down?
echo ""
echo "--- Shopify Status ---"
echo "Check: https://www.shopifystatus.com"
echo "API Status: https://www.shopifystatus.com/api/v2/status.json"
curl -sf "https://www.shopifystatus.com/api/v2/status.json" 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Overall: {d[\"status\"][\"description\"]}')" \
  2>/dev/null || echo "Could not reach status page"

# 2. Can we reach the Shopify API?
echo ""
echo "--- API Connectivity ---"
echo -n "Admin API: "
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/shop.json" 2>/dev/null)
echo "$HTTP_CODE"

# 3. Rate limit state
echo ""
echo "--- Rate Limit State ---"
curl -sI -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/shop.json" 2>/dev/null \
  | grep -i "x-shopify-shop-api-call-limit"

# 4. GraphQL rate limit
echo ""
echo "--- GraphQL Throttle ---"
curl -sf -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' \
  "https://$SHOPIFY_STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/graphql.json" 2>/dev/null \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
t=d.get('extensions',{}).get('cost',{}).get('throttleStatus',{})
print(f'Available: {t.get(\"currentlyAvailable\",\"?\")}/{t.get(\"maximumAvailable\",\"?\")}')
print(f'Restore rate: {t.get(\"restoreRate\",\"?\")}/sec')
" 2>/dev/null || echo "Could not query"
```
