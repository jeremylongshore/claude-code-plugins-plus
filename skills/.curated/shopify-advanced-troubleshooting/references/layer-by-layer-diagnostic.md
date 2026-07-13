Layer-by-layer diagnostic script that tests DNS, TCP, TLS, HTTP, GraphQL, and rate limit state independently.

```bash
#!/bin/bash
# shopify-layer-test.sh — test each layer independently
STORE="$SHOPIFY_STORE"
TOKEN="$SHOPIFY_ACCESS_TOKEN"
VERSION="2025-04"  # Update quarterly — see shopify.dev/docs/api/usage/versioning

echo "=== Layer-by-Layer Diagnostic ==="

# Layer 1: DNS
echo -n "1. DNS: "
dig +short "$STORE" >/dev/null 2>&1 && echo "OK" || echo "FAIL"

# Layer 2: TCP connectivity
echo -n "2. TCP: "
timeout 5 bash -c "echo > /dev/tcp/${STORE}/443" 2>/dev/null && echo "OK" || echo "FAIL"

# Layer 3: TLS handshake
echo -n "3. TLS: "
echo | openssl s_client -connect "$STORE:443" -servername "$STORE" 2>/dev/null | grep -q "Verify return code: 0" && echo "OK" || echo "FAIL"

# Layer 4: HTTP response
echo -n "4. HTTP: "
HTTP=$(curl -sf -o /dev/null -w "%{http_code}" "https://$STORE/admin/api/$VERSION/shop.json" -H "X-Shopify-Access-Token: $TOKEN")
[ "$HTTP" = "200" ] && echo "OK ($HTTP)" || echo "FAIL ($HTTP)"

# Layer 5: GraphQL
echo -n "5. GraphQL: "
GQL=$(curl -sf "https://$STORE/admin/api/$VERSION/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' | jq -r '.data.shop.name')
[ -n "$GQL" ] && echo "OK ($GQL)" || echo "FAIL"

# Layer 6: Rate limit state
echo -n "6. Rate limit: "
curl -sf "https://$STORE/admin/api/$VERSION/graphql.json" \
  -H "X-Shopify-Access-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ shop { name } }"}' \
  | jq -r '.extensions.cost.throttleStatus | "\(.currentlyAvailable)/\(.maximumAvailable) available"'
```
