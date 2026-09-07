# Intercom Diagnostics

A one-shot health check for an Intercom integration. Run it when you suspect
auth, rate-limit, or Intercom-side problems and want a fast triage before
digging into a specific error code.

## Quick Diagnostic Script

```bash
#!/bin/bash
TOKEN="${INTERCOM_ACCESS_TOKEN}"

echo "=== Intercom API Diagnostics ==="

# Test auth
echo -n "Auth: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  https://api.intercom.io/me)
echo "$STATUS $([ "$STATUS" = "200" ] && echo "OK" || echo "FAIL")"

# Check rate limits
echo -n "Rate limit remaining: "
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  https://api.intercom.io/me 2>/dev/null | grep -i x-ratelimit-remaining

# Intercom status
echo -n "Intercom status: "
curl -s https://status.intercom.com/api/v2/status.json | jq -r '.status.description'
```

## Reading the output

- **Auth: 200 OK** — token is valid; the failure is elsewhere (scope, payload, resource ID).
- **Auth: 401 FAIL** — token is expired, revoked, or wrong environment. See 401 in the error reference.
- **Rate limit remaining: 0** — you are throttled; apply exponential backoff (see 429).
- **Intercom status** anything other than "All Systems Operational" — an Intercom-side incident; retry with backoff and monitor the status page.
