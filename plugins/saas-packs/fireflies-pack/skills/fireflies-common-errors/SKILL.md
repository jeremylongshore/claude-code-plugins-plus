---
name: fireflies-common-errors
description: |
  Diagnose and fix Fireflies.ai GraphQL API errors by error code.
  Use when encountering Fireflies.ai errors, debugging failed requests,
  or troubleshooting authentication and rate limit issues.
  Trigger with phrases like "fireflies error", "fix fireflies",
  "fireflies not working", "debug fireflies", "fireflies 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, debugging]

---
# Fireflies.ai Common Errors

## Overview
Quick reference for all Fireflies.ai GraphQL API error codes with root causes and fixes.

## Error Response Format
All Fireflies errors follow this GraphQL error structure:
```json
{
  "errors": [{
    "message": "Human-readable description",
    "code": "error_code",
    "friendly": true,
    "extensions": {
      "status": 400,
      "helpUrls": ["https://docs.fireflies.ai/..."]
    }
  }]
}
```

## Error Code Reference

### `auth_failed` (401)
**Message:** Invalid or missing API key.
```bash
# Verify API key is set and valid
echo "Key set: ${FIREFLIES_API_KEY:+YES}"

# Test authentication
set -euo pipefail
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email } }"}' | jq .
```
**Fix:** Regenerate API key at app.fireflies.ai > Integrations > Fireflies API.

---

### `too_many_requests` (429)
**Message:** Rate limit exceeded.

| Plan | Limit |
|------|-------|
| Free / Pro | 50 requests per day |
| Business / Enterprise | 60 requests per minute |

**Fix:** Implement exponential backoff. See `fireflies-rate-limits` skill.

---

### `require_ai_credits` (402)
**Message:** AskFred operations require AI credits.
**Fix:** Visit Fireflies dashboard > Upgrade section to purchase AI credits. Budget for `createAskFredThread` and `continueAskFredThread` calls.

---

### `account_cancelled` (403)
**Message:** Subscription inactive.
**Fix:** Renew your Fireflies subscription or switch to a different API key.

---

### `invalid_language_code` (400)
**Message:** Unsupported language code in `uploadAudio` or `addToLiveMeeting`.
**Fix:** Use ISO 639-1 codes (e.g., `en`, `es`, `de`, `fr`, `ja`). Max 5 characters.

---

### `unsupported_platform` (400)
**Message:** Meeting platform not recognized by `addToLiveMeeting`.
**Fix:** Fireflies supports Google Meet, Zoom, and Microsoft Teams. Verify the `meeting_link` is a valid URL for one of these platforms.

---

### `payload_too_small` (400)
**Message:** Uploaded audio file is below 50KB minimum.
**Fix:** Set `bypass_size_check: true` in `AudioUploadInput` for short clips:
```typescript
await firefliesQuery(`
  mutation($input: AudioUploadInput) {
    uploadAudio(input: $input) { success title message }
  }
`, {
  input: {
    url: "https://example.com/short-clip.mp3",
    bypass_size_check: true,
  },
});
```

---

### GraphQL Validation Errors (400)
**Message:** Field or argument not found in schema.
```bash
# Introspect the schema to discover available fields
set -euo pipefail
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { fields { name description } } } }"}' | jq '.data.__schema.queryType.fields[] | {name, description}'
```

---

### Network / Connection Errors
| Symptom | Cause | Fix |
|---------|-------|-----|
| `ECONNREFUSED` | Firewall blocking | Allow outbound HTTPS to `api.fireflies.ai` |
| `ETIMEDOUT` | DNS or network issue | Check DNS resolution for `api.fireflies.ai` |
| `ENOTFOUND` | DNS failure | Verify DNS, try `8.8.8.8` resolver |

## Quick Diagnostic Script
```bash
set -euo pipefail
echo "=== Fireflies.ai Diagnostics ==="
echo "API Key: ${FIREFLIES_API_KEY:+SET (${#FIREFLIES_API_KEY} chars)}"
echo ""

# Connectivity
echo "--- Connectivity ---"
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email } }"}'

# Full response
echo ""
echo "--- Auth Check ---"
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { name email is_admin } }"}' | jq .
```

## Deprecated Fields
These fields still work but will be removed:
| Deprecated | Replacement |
|-----------|-------------|
| `transcript.host_email` | `transcript.organizer_email` |
| `transcripts(date: ...)` | `transcripts(fromDate: ..., toDate: ...)` |
| `transcripts(title: ...)` | `transcripts(keyword: ..., scope: ...)` |
| `transcripts(organizer_email: ...)` | `transcripts(organizers: [...])` |
| `transcripts(participant_email: ...)` | `transcripts(participants: [...])` |

## Output
- Error code identified with root cause
- Fix applied and verified
- Deprecated field warnings resolved

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Fireflies Introspection](https://docs.fireflies.ai/fundamentals/introspection)
- [Fireflies API Concepts](https://docs.fireflies.ai/fundamentals/concepts)

## Next Steps
For comprehensive debugging, see `fireflies-debug-bundle`.
