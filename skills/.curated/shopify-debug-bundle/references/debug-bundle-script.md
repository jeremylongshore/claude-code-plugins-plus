Complete bash script that collects Shopify diagnostic information into a shareable bundle.

```bash
#!/bin/bash
# shopify-debug-bundle.sh
set -euo pipefail

STORE="${SHOPIFY_STORE:-your-store.myshopify.com}"
TOKEN="${SHOPIFY_ACCESS_TOKEN}"
VERSION="${SHOPIFY_API_VERSION:-2025-04}"  # Update quarterly — see shopify.dev/docs/api/usage/versioning
BUNDLE_DIR="shopify-debug-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BUNDLE_DIR"

echo "=== Shopify Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Store: $STORE" | tee -a "$BUNDLE_DIR/summary.txt"
echo "API Version: $VERSION" | tee -a "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BUNDLE_DIR/summary.txt"
echo "---" | tee -a "$BUNDLE_DIR/summary.txt"

# --- Shop Info and Plan ---
echo "--- Shop Info ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/$VERSION/shop.json" \
  | jq '{name: .shop.name, plan: .shop.plan_name, domain: .shop.domain, timezone: .shop.iana_timezone}' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED: shop.json" >> "$BUNDLE_DIR/summary.txt"

# --- Granted Access Scopes ---
echo "--- Access Scopes ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/oauth/access_scopes.json" \
  | jq '.access_scopes[].handle' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED: scopes" >> "$BUNDLE_DIR/summary.txt"

# --- Supported API Versions ---
echo "--- API Versions ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/versions.json" \
  | jq '.supported_versions[] | {handle, display_name, latest, supported}' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED: versions" >> "$BUNDLE_DIR/summary.txt"

# --- GraphQL Rate Limit Check ---
echo "--- Rate Limit State ---" >> "$BUNDLE_DIR/summary.txt"
curl -sf -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' \
  "https://$STORE/admin/api/$VERSION/graphql.json" \
  | jq '.extensions.cost' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1

# --- REST Rate Limit Headers ---
echo "--- REST Rate Limit Headers ---" >> "$BUNDLE_DIR/summary.txt"
curl -sI -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/$VERSION/shop.json" \
  | grep -iE "(x-shopify-shop-api-call-limit|retry-after|x-request-id)" \
  >> "$BUNDLE_DIR/summary.txt" 2>&1

# --- Environment ---
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"

echo "--- @shopify/shopify-api ---" >> "$BUNDLE_DIR/summary.txt"
npm list @shopify/shopify-api 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "not installed" >> "$BUNDLE_DIR/summary.txt"

echo "--- Env Vars (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_API_KEY: ${SHOPIFY_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_API_SECRET: ${SHOPIFY_API_SECRET:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_ACCESS_TOKEN: ${SHOPIFY_ACCESS_TOKEN:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_SCOPES: ${SHOPIFY_SCOPES:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
echo "SHOPIFY_API_VERSION: ${SHOPIFY_API_VERSION:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"

# --- Package and Redact ---
find "$BUNDLE_DIR" -type f -exec sed -i 's/shpat_[a-f0-9]\{32\}/shpat_[REDACTED]/g' {} +

tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Contents:"
ls -la "$BUNDLE_DIR/"
echo ""
echo "Review before sharing — check for sensitive data!"
```
