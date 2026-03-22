---
name: hex-common-errors
description: |
  Diagnose and fix Hex common errors and exceptions.
  Use when encountering Hex errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "hex error", "fix hex",
  "hex not working", "debug hex".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Common Errors

## Error Reference

### 401 Unauthorized
**Cause:** Token invalid, expired, or missing.
**Fix:** Regenerate token in Hex workspace settings.

### 403 Forbidden — Read-Only Token
**Cause:** Token has "Read projects" scope but RunProject requires "Run projects".
**Fix:** Create new token with "Run projects" scope.

### 404 Not Found — Project
**Cause:** Project ID wrong or project not published.
**Fix:** Verify project ID. Only published projects can be run via API.

### 429 Too Many Requests
**Cause:** RunProject is limited to 20 requests/min, 60/hr.
**Fix:** Queue runs with delays. See `hex-rate-limits`.

### Run Status: ERRORED
**Cause:** SQL query, Python code, or connection error in the project.
**Fix:** Open the project in Hex UI and check the error in the run history.

### Run Status: KILLED
**Cause:** Run exceeded timeout or was manually cancelled.
**Fix:** Optimize slow queries. Increase timeout in API trigger.

## Quick Diagnostics

```bash
# Test token
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $HEX_API_TOKEN" \
  https://app.hex.tech/api/v1/projects

# List recent runs for a project
curl -s -H "Authorization: Bearer $HEX_API_TOKEN" \
  https://app.hex.tech/api/v1/project/PROJECT_ID/runs | python3 -m json.tool
```

## Resources

- [Hex API Reference](https://learn.hex.tech/docs/api/api-reference)

## Next Steps

For debugging, see `hex-debug-bundle`.
