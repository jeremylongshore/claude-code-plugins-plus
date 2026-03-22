---
name: fathom-common-errors
description: |
  Diagnose and fix Fathom API errors including auth failures and missing data.
  Use when API calls fail, transcripts are empty, or webhooks are not firing.
  Trigger with phrases like "fathom error", "fathom not working",
  "fathom api failure", "fix fathom".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Common Errors

## Error Reference

### 1. 401 Unauthorized
**Fix**: Regenerate API key at Settings > Integrations > API Access.

### 2. 429 Rate Limited
Limit: 60 calls per minute across all API keys.
**Fix**: Implement exponential backoff. Batch requests.

### 3. Empty Transcript
**Causes**: Meeting still processing, recording too short, or audio quality issues.
**Fix**: Wait 5-10 minutes after recording. Check recording in Fathom UI.

### 4. Missing Summary
**Cause**: AI processing not complete.
**Fix**: Poll the recording endpoint until summary is available.

### 5. Webhook Not Firing
**Fix**: Verify webhook URL in Settings > Integrations > Webhooks. Test with:
```bash
curl -X POST https://your-url.com/webhooks/fathom \
  -H "Content-Type: application/json" \
  -d '{"type": "test"}'
```

### 6. OAuth Token Expired
**Fix**: Refresh the access token using your refresh token.

## Quick Diagnostics

```bash
# Test API key
curl -s -o /dev/null -w "%{http_code}" -H "X-Api-Key: ${FATHOM_API_KEY}" \
  https://api.fathom.ai/external/v1/meetings?limit=1
```

## Resources

- [Fathom Help Center](https://help.fathom.video)
- [Fathom API Docs](https://developers.fathom.ai)

## Next Steps

For diagnostics, see `fathom-debug-bundle`.
