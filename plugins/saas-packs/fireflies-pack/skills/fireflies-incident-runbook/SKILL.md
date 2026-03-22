---
name: fireflies-incident-runbook
description: |
  Execute Fireflies.ai incident response with triage, remediation, and postmortem.
  Use when responding to Fireflies.ai API outages, auth failures,
  or webhook delivery problems.
  Trigger with phrases like "fireflies incident", "fireflies outage",
  "fireflies down", "fireflies on-call", "fireflies emergency", "fireflies broken".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, incident-response]

---
# Fireflies.ai Incident Runbook

## Overview
Rapid incident response procedures for Fireflies.ai integration failures. Covers API outages, authentication problems, webhook issues, and rate limiting.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Integration fully broken | < 15 min | `auth_failed` on all requests |
| P2 | Degraded functionality | < 1 hour | Rate limiting, slow responses |
| P3 | Minor impact | < 4 hours | Webhook delays, missing summaries |
| P4 | No user impact | Next business day | Monitoring gaps |

## Quick Triage (Run First)

```bash
set -euo pipefail
echo "=== Fireflies.ai Incident Triage ==="
echo ""

# 1. Can we reach the API?
echo "--- API Connectivity ---"
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)\n" \
  -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email } }"}'

# 2. What error are we getting?
echo ""
echo "--- API Response ---"
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email is_admin } }"}' | jq .

# 3. Can we list transcripts?
echo ""
echo "--- Transcript Access ---"
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ transcripts(limit: 1) { id title date } }"}' | jq '.data.transcripts[0] // .errors[0]'
```

## Decision Tree

```
API returning errors?
├─ YES: What error code?
│   ├─ auth_failed (401) → API key revoked or invalid
│   │   └─ Fix: Regenerate key at app.fireflies.ai > Integrations
│   ├─ too_many_requests (429) → Rate limited
│   │   └─ Fix: Enable backoff, check for runaway loops
│   ├─ account_cancelled (403) → Subscription expired
│   │   └─ Fix: Renew subscription, contact billing
│   └─ 5xx errors → Fireflies platform issue
│       └─ Fix: Enable fallback mode, wait for resolution
└─ NO: Webhook issues?
    ├─ Not receiving webhooks → Check dashboard registration
    ├─ Invalid signature → Webhook secret mismatch
    └─ Processing failures → Check your webhook handler logs
```

## Remediation by Error Type

### `auth_failed` (401) -- P1
```bash
set -euo pipefail
# Verify API key format (should be non-empty)
echo "Key length: ${#FIREFLIES_API_KEY}"

# Test with explicit key
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email } }"}' | jq '.errors[0].code // "OK"'

# Fix: Regenerate at app.fireflies.ai > Integrations > Fireflies API
# Then update your secret store:
# - GitHub: gh secret set FIREFLIES_API_KEY --body "new-key"
# - Vercel: vercel env rm FIREFLIES_API_KEY && vercel env add FIREFLIES_API_KEY
# - GCP: echo -n "new-key" | gcloud secrets versions add fireflies-api-key --data-file=-
```

### `too_many_requests` (429) -- P2
```bash
set -euo pipefail
# Check if we have a request loop
# Free/Pro: 50/day limit. Business: 60/min limit.
echo "Check application logs for request volume"

# Immediate mitigation: reduce request rate
# Long-term: implement exponential backoff (see fireflies-rate-limits skill)
```

### Webhook Not Firing -- P2
```bash
set -euo pipefail
# Verify webhook is registered
echo "Check: app.fireflies.ai > Settings > Developer settings"
echo "Webhook URL should be your HTTPS endpoint"

# Test by uploading audio (triggers webhook when done)
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: AudioUploadInput) { uploadAudio(input: $input) { success message } }",
    "variables": { "input": { "url": "https://example.com/test.mp3", "title": "Webhook Test" } }
  }' | jq .

# Remember: webhooks only fire for meetings YOU own (organizer_email)
```

### Invalid Webhook Signature -- P3
```typescript
// Debug signature verification
import crypto from "crypto";

function debugWebhookSignature(payload: string, receivedSig: string, secret: string) {
  const computed = crypto.createHmac("sha256", secret).update(payload).digest("hex");

  console.log("Received signature:", receivedSig);
  console.log("Computed signature:", computed);
  console.log("Match:", receivedSig === computed);
  console.log("Secret length:", secret.length, "(must be 16-32)");

  // Common issues:
  // 1. Secret doesn't match what's in Fireflies dashboard
  // 2. Payload was parsed/modified before verification (use raw body)
  // 3. Secret has trailing whitespace
}
```

## Communication Templates

### Internal (Slack)
```
P[1-4] INCIDENT: Fireflies.ai Integration
Status: INVESTIGATING / MITIGATED / RESOLVED
Error: [error code and message]
Impact: [what users are affected]
Action: [what we're doing]
ETA: [next update time]
```

### Postmortem Template
```markdown
## Incident: Fireflies.ai [Error Type]
**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]

### Summary
[1-2 sentences]

### Timeline
- HH:MM - Issue detected via [alert/user report]
- HH:MM - Triage started
- HH:MM - Root cause identified: [cause]
- HH:MM - Fix applied
- HH:MM - Verified resolved

### Root Cause
[Technical explanation]

### Action Items
- [ ] [Prevention measure] - Owner - Due date
```

## Error Handling
| Issue | Response |
|-------|----------|
| Can't run triage script | Check `FIREFLIES_API_KEY` is set, check network |
| Multiple error codes | Address auth first, then rate limits |
| Intermittent failures | May be transient -- monitor for 15 min before escalating |
| All endpoints failing | Likely Fireflies platform issue -- enable fallback mode |

## Output
- Issue identified and categorized by severity
- Remediation applied based on error code
- Stakeholders notified via templates
- Evidence collected for postmortem

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Fireflies Webhooks](https://docs.fireflies.ai/graphql-api/webhooks)

## Next Steps
For data handling and compliance, see `fireflies-data-handling`.
