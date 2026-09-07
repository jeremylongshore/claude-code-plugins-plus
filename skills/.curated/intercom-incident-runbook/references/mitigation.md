# Mitigation by Error Type & Graceful Degradation

Deep reference for the mitigation phase. Each block is scoped to a specific HTTP
status class returned by the Intercom API.

## Mitigation by Error Type

### 401 - Authentication Failed

```bash
# Verify token is valid
curl -s -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me | jq '.type'
# Expected: "admin"
# If error: Token is invalid or revoked

# IMMEDIATE: Regenerate token
# Developer Hub > Your App > Authentication > Generate new token
# Update in secret manager:
aws secretsmanager update-secret \
  --secret-id intercom/production/token \
  --secret-string "new_token_here"

# Restart application to pick up new token
kubectl rollout restart deployment/intercom-service
```

### 429 - Rate Limited

```bash
# Check rate limit headers
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i "x-ratelimit"

# Immediate: Reduce request volume
# - Pause any batch/sync jobs
# - Enable request queuing if available

# Check if multiple apps are consuming workspace quota
# Limit: 25,000 req/min per workspace across all apps
```

### 5xx - Intercom Server Errors

```bash
# 1. Check Intercom status
curl -s https://status.intercom.com/api/v2/status.json | jq

# 2. Enable graceful degradation
# Your app should serve cached data or fallback UI

# 3. Track request_id from error responses for Intercom support
# Error response includes: { "request_id": "req_abc123" }
```

## Graceful Degradation Pattern

```typescript
import { IntercomClient, IntercomError } from "intercom-client";
import { LRUCache } from "lru-cache";

const cache = new LRUCache<string, any>({ max: 10000, ttl: 3600000 }); // 1hr fallback

async function getContactWithFallback(contactId: string): Promise<any> {
  try {
    const contact = await client.contacts.find({ contactId });
    cache.set(contactId, contact); // Update cache on success
    return contact;
  } catch (err) {
    if (err instanceof IntercomError && (err.statusCode === 429 || (err.statusCode ?? 0) >= 500)) {
      // Return stale cached data during outages
      const cached = cache.get(contactId);
      if (cached) {
        console.warn(`[Intercom] Serving cached data for ${contactId} due to ${err.statusCode}`);
        return { ...cached, _stale: true };
      }
    }
    throw err;
  }
}
```
