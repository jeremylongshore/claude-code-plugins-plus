# Pre-Deploy Smoke Test

Bash script that validates Shopify auth, API scopes, and connectivity before deploying to production.

```bash
#!/bin/bash
echo "=== Shopify Pre-Deploy Smoke Test ==="
STORE="$SHOPIFY_STORE"
TOKEN="$SHOPIFY_ACCESS_TOKEN"
PASS=0; FAIL=0

# Auth test — use a recent stable API version (e.g., 2025-04)
if curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/2025-04/shop.json" > /dev/null; then
  echo "PASS: Auth"; ((PASS++))
else
  echo "FAIL: Auth"; ((FAIL++))
fi

# Scopes test
SCOPES=$(curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/oauth/access_scopes.json" | jq -r '.access_scopes[].handle')
for required in read_products read_orders; do
  if echo "$SCOPES" | grep -q "$required"; then
    echo "PASS: Scope $required"; ((PASS++))
  else
    echo "FAIL: Missing scope $required"; ((FAIL++))
  fi
done

echo "---"
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "READY FOR DEPLOY" || echo "FIX FAILURES FIRST"
```
