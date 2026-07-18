---
name: apify-common-errors
description: |
  Diagnose and fix common Apify Actor and API errors.
  Use when an Apify run fails, an API call returns 401/403/404/413/429,
  a proxy connection drops, an Actor build breaks, or a scrape hits an
  anti-bot block, and you need the cause plus a copy-paste fix.
  Trigger with "apify error", "fix apify", "actor failed",
  "apify not working", "debug apify", "apify 429".
allowed-tools: Bash(curl:*), Bash(apify:*), Bash(npm:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Common Errors

## Overview

Quick diagnostic reference for the most common Apify errors. Covers Actor run
failures, API errors, proxy problems, anti-bot blocks, and platform-specific
issues. The full per-error catalog — raw signature, cause, diagnosis, and
copy-paste fix for all ten errors — lives in
[references/error-reference.md](references/error-reference.md); this file is the
lean triage path that points you there.

## Prerequisites

- An Apify API token exported as `APIFY_TOKEN` (Console > Settings > Integrations).
- Access to the [Apify Console](https://console.apify.com) for reading run and build logs.
- `curl` and `jq` on PATH for the diagnostic commands below; `apify` CLI optional for build inspection.

## Instructions

Work the failure from signal to fix:

1. **Capture the exact error.** Grab the `Status` / `StatusMessage` from the
   run, or the `ApifyApiError` message and HTTP code from the API response.
   The raw string is the key you match on.
2. **Match the signature.** Find the matching entry in the table below, then
   open [references/error-reference.md](references/error-reference.md) at that
   number for the cause, diagnosis, and fix.
3. **Diagnose before changing code.** For run failures, pull the log via the
   API or Console (see the FAILED entry). For auth/rate/payload errors, the
   HTTP code already tells you the class — see [Error Handling](#error-handling).
4. **Apply the fix from the reference,** re-run, and confirm with the
   [diagnostic commands](#examples).

### Error signature → reference

| # | Error | Signature to match |
|---|-------|--------------------|
| 1 | Actor run FAILED | `Status: FAILED` / `exited with code 1` |
| 2 | Actor run TIMED-OUT | `Actor timed out after N seconds` |
| 3 | Rate limited | `Rate limit exceeded (429)` |
| 4 | Unauthorized | `Authentication required (401)` |
| 5 | Build failed | `Build failed: npm ERR!` |
| 6 | Proxy connection failed | `502 Bad Gateway` / `Could not connect to proxy` |
| 7 | Anti-bot block | `status 403` / `Captcha detected` |
| 8 | Out of memory | `JavaScript heap out of memory` |
| 9 | Dataset push too large | `Payload too large (413)` |
| 10 | Actor not found | `Actor '…' not found (404)` |

Full detail for every row: [references/error-reference.md](references/error-reference.md).

## Output

Working through this skill yields:

- The identified error class (matched signature + the one of ten catalog entries).
- The root cause and a copy-paste fix (config change, code edit, or token/proxy action).
- A verification command whose output confirms the run recovered (status `SUCCEEDED`, valid `username`, etc.).

## Error Handling

| HTTP Code | Meaning | Retryable | Action |
|-----------|---------|-----------|--------|
| 400 | Bad request | No | Fix input/params |
| 401 | Unauthorized | No | Check token |
| 403 | Forbidden | No | Check permissions |
| 404 | Not found | No | Verify resource ID |
| 408 | Timeout | Yes | Retry with backoff |
| 413 | Payload too large | No | Reduce batch size |
| 429 | Rate limited | Yes | Auto-retried by client |
| 500+ | Server error | Yes | Auto-retried by client |

## Examples

Diagnostic commands for the most common triage steps:

```bash
# Check Apify platform status
curl -s https://api.apify.com/v2/health | jq '.'

# Verify your auth (fixes 401 diagnosis)
curl -s -H "Authorization: Bearer $APIFY_TOKEN" \
  https://api.apify.com/v2/users/me | jq '.data.username'

# Check installed package versions
npm list apify-client apify crawlee 2>/dev/null

# Get last run status (find why a run FAILED / TIMED-OUT)
curl -s -H "Authorization: Bearer $APIFY_TOKEN" \
  "https://api.apify.com/v2/acts/USER~ACTOR/runs?limit=1&desc=true" | \
  jq '.data.items[0] | {status, statusMessage, startedAt, finishedAt}'
```

For the worked fix behind each error — e.g. reading a run log to find a stack
trace, batching dataset pushes under 9MB, or switching to residential proxies to
clear a 403 — see the matching entry in
[references/error-reference.md](references/error-reference.md).

## Resources

- [Apify API Error Codes](https://docs.apify.com/api/v2)
- [Apify Status Page](https://status.apify.com)
- [Actor Run Statuses](https://docs.apify.com/platform/actors/running)
- [Full error catalog (all 10, with fixes)](references/error-reference.md)

## Next Steps

For comprehensive multi-error debugging across a whole Actor project — log
correlation, proxy rotation strategy, and build-cache issues — see the
`apify-debug-bundle` skill in this pack.
</content>
