---
name: persona-common-errors
description: |
  Fix top Persona API errors: 401, 422, webhook signature failures, inquiry state issues.
  Use when working with Persona identity verification.
  Trigger with phrases like "persona common-errors", "persona common-errors".
allowed-tools: Read, Grep, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, verification]
compatible-with: claude-code, codex, openclaw
---

# persona common errors | sed 's/\b\(.\)/\u\1/g'

## Overview
401 invalid key, 422 invalid template, webhook HMAC mismatch, inquiry already completed, rate limit 429.

## Prerequisites
- Completed `persona-install-auth` setup
- Valid Persona API key (sandbox or production)

## Instructions

### Error 1: 401 Unauthorized
```
{"errors":[{"status":"401","title":"Not Authorized"}]}
```
**Fix:** Verify API key starts with `persona_sandbox_` or `persona_production_`. Check `Authorization: Bearer <key>` header format.

### Error 2: 422 Invalid Inquiry Template
```
{"errors":[{"status":"422","title":"Invalid inquiry-template-id"}]}
```
**Fix:** Verify template ID format is `itmpl_*`. Templates are environment-specific (sandbox templates only work with sandbox keys).

### Error 3: Webhook Signature Mismatch
```
HMAC verification failed — expected abc123, got def456
```
**Fix:** Ensure you're using the raw request body (not parsed JSON) for HMAC computation. Use `express.raw()` middleware.

### Error 4: 429 Rate Limited
```
{"errors":[{"status":"429","title":"Rate limit exceeded"}]}
```
**Fix:** Implement exponential backoff. Check `Retry-After` header. See `persona-rate-limits`.

### Error 5: Inquiry Already Completed
```
{"errors":[{"status":"409","title":"Inquiry is already in a terminal state"}]}
```
**Fix:** Check inquiry status before attempting operations. Use the resume endpoint only for `created` or `pending` inquiries.

### Error 6: 404 Inquiry Not Found
```
{"errors":[{"status":"404","title":"Not Found"}]}
```
**Fix:** Verify inquiry ID format is `inq_*`. Sandbox inquiries are not accessible with production keys.

## Output
- Error identified from API response
- Targeted fix applied
- Verified resolution

## Error Handling
| HTTP Code | Meaning | Retryable |
|-----------|---------|-----------|
| 400 | Bad request | No |
| 401 | Invalid API key | No — fix key |
| 404 | Resource not found | No |
| 409 | Conflict (terminal state) | No |
| 422 | Validation error | No — fix request |
| 429 | Rate limited | Yes |
| 500+ | Server error | Yes |

## Resources
- [Persona API Reference](https://docs.withpersona.com/reference/introduction)

## Next Steps
For debugging, see `persona-debug-bundle`.
