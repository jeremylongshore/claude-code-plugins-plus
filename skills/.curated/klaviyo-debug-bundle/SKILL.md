---
name: klaviyo-debug-bundle
description: 'Collect Klaviyo debug evidence for support tickets and troubleshooting.

  Use when a Klaviyo integration is failing, when preparing a support ticket,

  or when collecting diagnostic information for a Klaviyo API problem.

  Trigger with phrases like "klaviyo debug", "klaviyo support bundle",

  "collect klaviyo logs", "klaviyo diagnostic", "klaviyo troubleshoot".

  '
allowed-tools: Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(npm:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Debug Bundle

## Overview

Collect all diagnostic information needed for a Klaviyo support ticket into one
redacted, shareable tarball: SDK version, API connectivity, auth result, rate
limit status, recent errors, and environment config. Every secret (API keys,
emails, phone numbers, webhook secrets) is redacted before packaging, so the
bundle is safe to attach to a ticket.

The workflow builds a single shell script (`klaviyo-debug-bundle.sh`) in five
steps, then runs it. The full script and a programmatic TypeScript alternative
live in the reference files linked below.

## Prerequisites

- The `klaviyo-api` SDK installed (`npm list klaviyo-api` to confirm).
- The `KLAVIYO_PRIVATE_KEY` environment variable set to a private API key.
- Read access to your application's log directory (defaults scanned: `logs/`,
  `/var/log/app/`).
- `curl`, `tar`, and `python3` available on the host.

## Instructions

Assemble the five blocks below (verbatim from the reference) into one
`klaviyo-debug-bundle.sh`, make it executable, and run it from your application
root so the log-collection step can find `logs/`.

1. **Create the bundle dir** — timestamped `klaviyo-debug-YYYYMMDD-HHMMSS/` and a `summary.txt` header.
2. **Collect environment info** — Node/npm/OS versions, `klaviyo-api` SDK version, and a redacted API-key presence check.
3. **Run connectivity tests** — DNS resolve, an authenticated `GET /api/accounts/` (captures the HTTP code), rate-limit headers, and the Klaviyo status page.
4. **Collect logs** — grep known log dirs for Klaviyo errors, redacting keys and emails inline.
5. **Package and clean up** — `tar -czf` the dir, remove the working copy, print the tarball path.

The skeleton of step 1:

```bash
#!/bin/bash
# klaviyo-debug-bundle.sh
set -euo pipefail
BUNDLE_DIR="klaviyo-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
```

See the [full shell implementation](references/implementation.md) for all five
steps verbatim. To collect the same signals as a structured object (SDK version,
connectivity, latency) instead of a tarball, use the TypeScript helper in
[examples](references/examples.md).

## Output

- `klaviyo-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` -- Environment, SDK version, API key status, connectivity
  - `rate-limits.txt` -- Current rate limit header values
  - `api-response.json` -- Account API response (confirms auth)
  - `recent-errors.txt` -- Redacted error logs

### Redaction rules

**ALWAYS redacted:** API keys (`pk_***`), email addresses, phone numbers, webhook secrets.

**Safe to include:** error/HTTP status codes, SDK and runtime versions, stack
traces (with PII redacted), rate limit header values, Klaviyo account ID.

## Error Handling

The bundle is designed to never abort on a single failed probe — each check
records its failure into the summary rather than exiting, so you always get a
complete picture. Read the results with this triage:

- **`KLAVIYO_PRIVATE_KEY: NOT SET`** — the connectivity and rate-limit steps are
  skipped. Export the key and re-run before attaching the bundle.
- **`API Auth Test: HTTP 401`** — key is invalid or revoked. Rotate the key.
- **`API Auth Test: HTTP 403`** — key lacks scope for `/api/accounts/`. Grant the
  scope in Klaviyo account settings.
- **`API Auth Test: HTTP 429`** — you are rate limited; inspect `rate-limits.txt`
  and see the `klaviyo-rate-limits` skill.
- **`API Auth Test: HTTP 000` or `DNS resolve ... FAILED`** — no response reached
  Klaviyo (DNS, outbound firewall, or TLS). Fix connectivity before ticketing.
- **`recent-errors.txt` empty** — no matching log dir was found; pass your real
  log path by adding it to the `for logdir in ...` loop in step 4.
- **Before sharing**, open `summary.txt` and confirm no unredacted `pk_` prefix
  or email survived — the script prints a reminder to do this.

See the [examples reference](references/examples.md) for the full HTTP-code
decision matrix.

## Examples

- **Generate a bundle for a failing send** — set the key, run the script, read
  the `HTTP 200` / `All Systems Operational` summary lines.
- **Programmatic debug info** — call `collectKlaviyoDebugInfo()` from a health
  check to return SDK version, connectivity, and latency as an object.
- **Reading the auth result** — map the `API Auth Test: HTTP NNN` line to a next
  action (200 healthy → check logs; 401 → rotate key; 429 → rate limits).

Full runnable code for all three is in [examples](references/examples.md).

## Resources

- Klaviyo Support Portal
- [Klaviyo Status Page](https://status.klaviyo.com)
- [API Error Alerts](https://developers.klaviyo.com/en/docs/review_api_error_alerts)
- [Full shell implementation](references/implementation.md)
- [Examples and error-triage table](references/examples.md)

## Next Steps

For rate limit issues surfaced by the bundle (`HTTP 429`, `retry-after` headers),
see the `klaviyo-rate-limits` skill for backoff and quota-management guidance.
