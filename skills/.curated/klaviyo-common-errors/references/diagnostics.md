# Klaviyo Diagnostics & SDK Errors

Reference companion to the error catalog: SDK-level (client-side) failures that
never reach the network, the copy-paste diagnostic commands, and the support
escalation path.

## Common SDK-Level Errors

These fail before or during the request in your own process — the fix is in your
code or dependencies, not in Klaviyo's response.

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module 'klaviyo-api'` | Wrong package | `npm install klaviyo-api` (not `@klaviyo/sdk`) |
| `TypeError: ... is not a constructor` | Wrong import | Use `new ProfilesApi(session)` not `new KlaviyoClient()` |
| `response.data is undefined` | Wrong access pattern | Use `response.body.data` (not `response.data`) |
| `filter is not valid` | Bad filter syntax | Use `equals(field,"value")` not `field = value` |

## Quick Diagnostic Commands

```bash
# Check Klaviyo API health
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/"

# Check Klaviyo status page
curl -s https://status.klaviyo.com/api/v2/status.json | python3 -m json.tool

# Verify local env
env | grep KLAVIYO
npm list klaviyo-api
```

## Escalation Path

1. Collect evidence with `klaviyo-debug-bundle`
2. Check [status.klaviyo.com](https://status.klaviyo.com)
3. Open ticket at Klaviyo Support with request IDs from error responses
