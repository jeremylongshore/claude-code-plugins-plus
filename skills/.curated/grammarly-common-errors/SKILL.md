---
name: grammarly-common-errors
description: 'Diagnose and fix Grammarly common errors and exceptions.

  Use when encountering Grammarly errors, debugging failed requests,

  or troubleshooting integration issues.

  Trigger with phrases like "grammarly error", "fix grammarly",

  "grammarly not working", "debug grammarly".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- grammarly
- writing
compatibility: Designed for Claude Code
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

## Overview

This reference triages common integration failures without retaining the text, suggestions, credentials, or account metadata that caused them. Use a bounded synthetic input and correlation IDs for every diagnostic.

## Prerequisites

- A synthetic test string, redacted correlation ID, endpoint class, and HTTP status.
- A scoped read-only diagnostic credential and a named owner for configuration or access changes.

## Instructions

1. Classify the status and operation before modifying a client, credential, or retry policy.
2. Reproduce once with synthetic input; capture only status, latency band, quota state, and correlation ID.
3. Check scope, request shape, size limit, quota, and asynchronous job state in that order.
4. Apply one reversible change at a time and escalate with a redacted bundle if the failure persists.

## Output

Return error class, correlation ID, environment, probe outcome, remediation attempted, and next owner. Do not include text, suggestions, tokens, or identities.

## Error Handling

Treat unknown destination, failed redaction, access-scope change, or repeated non-idempotent request as a stop condition. Do not retry by broadening access or logging rejected text.

## Examples

`status=413; env=sandbox; correlation=req-opaque-11; action=bounded-chunking; synthetic_probe=recovered` supports a safe handoff.

## Resources

- Grammarly API Support

## Next Steps

For debugging tools, see `grammarly-debug-bundle`.
