Quick diagnostic script that tests auth, scopes, API versions, and Shopify status in one pass.

```bash
#!/bin/bash
STORE="your-store.myshopify.com"
TOKEN="$SHOPIFY_ACCESS_TOKEN"
VERSION="2025-04"  # Update quarterly — see shopify.dev/docs/api/usage/versioning

echo "=== Shopify Diagnostic ==="

# 1. Test auth
echo -n "Auth: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/$VERSION/shop.json"
echo ""

# 2. Check scopes
echo "Scopes:"
curl -s -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/oauth/access_scopes.json" | python3 -m json.tool

# 3. Check API versions
echo "API Versions:"
curl -s -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/versions.json" | python3 -c "
import json, sys
versions = json.load(sys.stdin)['supported_versions']
for v in versions[:5]:
    print(f'  {v[\"handle\"]} {\"(latest)\" if v.get(\"latest\") else \"\"}')"

# 4. Shopify status
echo "Shopify Status: https://www.shopifystatus.com"
```
