---
name: grammarly-common-errors
description: |
  Diagnose and fix Grammarly common errors and exceptions.
  Use when encountering Grammarly errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "grammarly error", "fix grammarly",
  "grammarly not working", "debug grammarly".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Common Errors

## Error Reference

### 400 Bad Request — Text Too Short
**Cause:** Text has fewer than 30 words.
**Fix:** Ensure minimum 30 words. Pad short texts with context if needed.

### 401 Unauthorized
**Cause:** Token expired or invalid.
**Fix:** Re-authenticate with client credentials grant.

### 413 Payload Too Large
**Cause:** Text exceeds 100,000 characters or 4 MB.
**Fix:** Split into chunks using paragraph boundaries. See `grammarly-sdk-patterns` for chunking function.

### 429 Too Many Requests
**Cause:** Rate limit exceeded.
**Fix:** Implement exponential backoff. See `grammarly-rate-limits`.

### Plagiarism Check Stuck on "pending"
**Cause:** Large document processing or service delay.
**Fix:** Poll every 3-5 seconds, timeout after 90 seconds.

### AI Detection — Inconsistent Scores
**Cause:** Short text produces unreliable results.
**Fix:** AI detection works best on 200+ words. Scores on short text are less reliable.

## Quick Diagnostics

```bash
# Test API connectivity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $GRAMMARLY_ACCESS_TOKEN" \
  https://api.grammarly.com/ecosystem/api/v2/scores

# Test with sample text
curl -X POST https://api.grammarly.com/ecosystem/api/v2/scores \
  -H "Authorization: Bearer $GRAMMARLY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test sentence that has more than thirty words so that the API will accept it and return a valid writing score for our diagnostic purposes."}' | python3 -m json.tool
```

## Resources

- [Grammarly API Support](https://developer.grammarly.com/docs/support)

## Next Steps

For debugging tools, see `grammarly-debug-bundle`.
