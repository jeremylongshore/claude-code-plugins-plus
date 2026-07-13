# Immediate Actions by Error Type

Diagnostic commands and remediation steps for each common Shopify incident error type.

## 401 — Token Expired/Revoked

```bash
# Verify the token is still valid
curl -sf -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/shop.json" | jq '.shop.name'

# If 401: merchant may have uninstalled and reinstalled
# → Trigger re-authentication flow
# → Check APP_UNINSTALLED webhook logs
```

## 429 — Rate Limited

```bash
# Check if you have a runaway loop
# Look for rapid sequential API calls in your logs

# Immediate mitigation: pause all non-critical API calls
# Check GraphQL query costs — are any queries > 500 points?

# For REST: check the bucket header
curl -sI -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/shop.json" \
  | grep "x-shopify-shop-api-call-limit"
# If "40/40" — bucket is full, wait 20 seconds (40 / 2 per second)
```

## 5xx — Shopify Internal Error

```bash
# Capture the X-Request-Id for support
curl -sI -H "X-Shopify-Access-Token: $TOKEN" \
  "https://$STORE/admin/api/${SHOPIFY_API_VERSION:-2025-04}/shop.json" \
  | grep -i "x-request-id"
# Include this ID when contacting Shopify Partner Support
```
