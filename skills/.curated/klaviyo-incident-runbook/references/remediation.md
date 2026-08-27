# Immediate Actions by Error Type

Copy-paste remediation for the three error types that account for nearly every
Klaviyo integration incident: 401 (auth), 429 (rate limit), and 5xx (Klaviyo
server error). Each block is safe to run against production during an incident.

The `revision: 2024-10-15` header pins the request to a dated Klaviyo API
version; keep it identical to the value your application ships so the auth test
reproduces production behavior exactly.

## 401 -- Authentication Failure

```bash
# 1. Verify API key is set
echo "Key length: ${#KLAVIYO_PRIVATE_KEY} chars"
echo "Key prefix: ${KLAVIYO_PRIVATE_KEY:0:3}"

# 2. Test the key directly
curl -s -w "\nHTTP %{http_code}\n" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"

# 3. If key is invalid: generate new key in Klaviyo dashboard
# Settings > API Keys > Create Private API Key

# 4. Update in deployment platform
# GCP: echo -n "pk_new_***" | gcloud secrets versions add klaviyo-key --data-file=-
# AWS: aws secretsmanager update-secret --secret-id klaviyo-key --secret-string "pk_new_***"

# 5. Restart application to pick up new key
```

## 429 -- Rate Limited

```bash
# 1. Check current rate limit
curl -s -I \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
  | grep -i "ratelimit\|retry-after"

# 2. Reduce request volume immediately
# - Lower queue concurrency
# - Enable request sampling
# - Pause non-critical background jobs

# 3. Check for runaway processes
# Look for loops making excessive API calls
```

## 5xx -- Klaviyo Server Error

```bash
# 1. Check Klaviyo status page
curl -s "https://status.klaviyo.com/api/v2/status.json" | python3 -m json.tool

# 2. Enable graceful degradation
# Your app should continue working without Klaviyo
# Queue failed requests for retry when Klaviyo recovers

# 3. Monitor for recovery
watch -n 30 'curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"'
```
