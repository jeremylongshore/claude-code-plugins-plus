Post-deployment verification script that checks health, webhooks, and OAuth endpoints.

```bash
#!/bin/bash
APP_URL="https://your-app.example.com"

echo "=== Post-Deploy Verification ==="

# Health check
echo -n "Health: "
curl -sf "$APP_URL/health" | jq '.status'

# Webhook endpoint reachable
echo -n "Webhook endpoint: "
curl -sf -o /dev/null -w "%{http_code}" -X POST "$APP_URL/webhooks"
echo " (expected 401 — no HMAC)"

# OAuth start
echo -n "OAuth: "
curl -sf -o /dev/null -w "%{http_code}" "$APP_URL/auth?shop=test.myshopify.com"
echo ""

# Run shopify app config sync
echo "Syncing app config..."
shopify app deploy --force
```
