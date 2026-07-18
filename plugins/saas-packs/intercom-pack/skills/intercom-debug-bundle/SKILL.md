---
name: intercom-debug-bundle
description: 'Collect Intercom debug evidence for support tickets and troubleshooting.

  Use when encountering persistent Intercom API issues, auth or rate-limit

  failures, or preparing a diagnostic bundle to attach to an Intercom support

  ticket.

  Trigger with phrases like "intercom debug", "intercom support bundle",

  "collect intercom logs", "intercom diagnostic", "intercom troubleshoot".

  '
allowed-tools: Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(npm:*), Bash(node:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Debug Bundle

## Overview

Collect diagnostic evidence for Intercom issues: API health, auth status, rate-limit headers, SDK version, platform incidents, and redacted logs — packaged as a timestamped tarball safe to attach to a support ticket. Most persistent failures are auth (401) or rate-limit (429) problems, so the bundle leads with the `/me` health check before collecting anything heavier.

## Prerequisites

- Intercom access token exported as `INTERCOM_ACCESS_TOKEN`
- `curl` and `jq` available
- Access to application logs (optional — the collector redacts them)

## Instructions

### Step 1: Confirm auth before collecting

Most failed bundles are a bad token. Confirm `/me` returns `200` first; if not, fix auth before running the full collector.

```bash
TOKEN="${INTERCOM_ACCESS_TOKEN:?set INTERCOM_ACCESS_TOKEN and re-run}"
curl -s -o /dev/null -w "Auth HTTP: %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" \
  https://api.intercom.io/me
# 200 = OK, 401 = regenerate the token in the Developer Hub
```

### Step 2: Run the full bundle collector

When the quick check passes, run the seven-step collector. It writes token
status, auth JSON, rate-limit headers, platform status and active incidents,
environment/SDK info, endpoint latencies, and redacted logs into a timestamped
directory, then tars it up as `intercom-debug-YYYYMMDD-HHMMSS.tar.gz`. Tokens,
emails, and `.env` values are stripped before packaging.

See the complete `intercom-debug-bundle.sh` script (all seven steps) in
[full implementation](references/implementation.md).

### Step 3: Redact and review before sharing

The collector redacts as it goes, but review the tarball before attaching it to
a ticket. What to ALWAYS redact vs what is SAFE TO INCLUDE (with copy-paste
`curl` snippets for reading rate-limit headers and capturing a `request_id`)
lives in [examples and redaction rules](references/examples.md).

## Output

- `intercom-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` — token status, auth result, rate-limit headers, platform status, active incident count, environment, SDK version, and per-endpoint latency (`/me`, `/contacts`, `/conversations`, `/admins`)
  - `logs-redacted.txt` — recent Intercom-related log lines with tokens and emails masked (present only if `logs/app.log` exists)
  - `config-redacted.txt` — `.env` copy with all values masked (present only if `.env` exists)

## Sensitive Data Policy

**ALWAYS redact:** access tokens, OAuth secrets, webhook signing secrets, email addresses and PII, customer conversation content.

**Safe to include:** HTTP status/error codes, `request_id` from error responses (Intercom support needs these), rate-limit header values, SDK/runtime versions, endpoint latencies. Full rules in [examples and redaction rules](references/examples.md).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `jq: command not found` | jq not installed | `apt install jq` or `brew install jq` |
| Auth test returns 401 | Token invalid | Regenerate in Developer Hub |
| Status page unreachable | Network issue | Try `curl https://status.intercom.com` directly |
| No rate limit headers | Request failed early | Fix auth first |

## Examples

Quick reference for the most common check — confirm the token authenticates:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
  https://api.intercom.io/me
# 200 = OK, 401 = regenerate token
```

For reading rate-limit headers, capturing a `request_id` from an error response,
and the full redaction rules, see
[examples and redaction rules](references/examples.md).

## Resources

- [Intercom Status](https://status.intercom.com) — real-time platform health and incidents
- [Intercom Support](https://www.intercom.com/help) — help center and ticket submission
- [Error Codes Reference](https://developers.intercom.com/docs/references/rest-api/errors/error-codes) — full REST API error code list

## Next Steps

For rate limit handling, see `intercom-rate-limits`. For auth setup, see `intercom-install-auth`.
