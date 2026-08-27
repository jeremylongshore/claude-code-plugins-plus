---
name: hex-common-errors
description: 'Diagnose and fix Hex common errors and exceptions.

  Use when encountering Hex errors, debugging failed requests,

  or troubleshooting integration issues.

  Trigger with phrases like "hex error", "fix hex",

  "hex not working", "debug hex".

  '
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hex
- data
- analytics
compatibility: Designed for Claude Code
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

## Overview

This reference triages project-run failures using status, aggregate telemetry, and opaque run IDs. It does not authorize copying SQL, cell output, data previews, or tokens into a ticket.

## Prerequisites

- A safe sandbox probe, redacted correlation ID, endpoint class, and HTTP or terminal-run status.
- A scoped read-only diagnostic credential and named owner for any project, schedule, or access change.

## Instructions

1. Classify authentication, authorization, project lookup, validation, quota, timeout, and terminal-run errors before changing configuration.
2. Reproduce once with the safe probe and capture only status, latency, quota, and opaque run ID.
3. Check scope, parameter schema, project state, quota, and downstream connection health in that order.
4. Make one reversible change at a time and escalate a redacted bundle when the error persists.

## Output

Return error class, correlation ID, project scope, probe outcome, remediation attempted, and next owner. Do not include SQL, output, credentials, or identities.

## Error Handling

Treat unknown destination, failed redaction, access expansion, or repeated non-idempotent run as a stop condition. Cancel or restore the prior revision rather than retrying with broader scope.

## Examples

`status=429; project=proj-sandbox-12; correlation=run-opaque-11; action=bounded-backoff; safe_probe=recovered` supports a safe handoff.

## Resources

- [Hex API Reference](https://learn.hex.tech/docs/api/api-reference)

## Next Steps

For debugging, see `hex-debug-bundle`.
