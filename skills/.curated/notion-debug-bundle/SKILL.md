---
name: notion-debug-bundle
description: 'Collect Notion API diagnostic info for troubleshooting and support tickets.

  Use when encountering persistent API issues, token/auth failures, page access

  problems, or preparing diagnostic bundles for Notion support.

  Trigger with phrases like "notion debug", "notion diagnostic", "notion support

  bundle", "collect notion logs", "notion troubleshoot".

  '
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(npm:*), Bash(node:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Debug Bundle

## Overview

Collect diagnostic information for Notion API issues: SDK version, token validity, database access, page sharing status, rate limits, and platform health. The Notion API requires integrations to be explicitly invited to each page or database — most "not found" errors are sharing problems, not code bugs.

## Prerequisites

- `@notionhq/client` installed (`npm ls @notionhq/client` to verify)
- `NOTION_TOKEN` environment variable set (internal integration token, starts with `ntn_`)
- `curl` and `jq` available for shell-based diagnostics

## Instructions

### Step 1: Quick Connectivity and Auth Check

```bash
#!/bin/bash
echo "=== Notion Debug Check ==="
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. SDK version
echo -e "\n--- SDK Version ---"
npm ls @notionhq/client 2>/dev/null || echo "SDK not found — run: npm install @notionhq/client"

# 2. Runtime and token status
echo -e "\n--- Runtime ---"
node --version 2>/dev/null || echo "Node.js not found"
echo "NOTION_TOKEN: ${NOTION_TOKEN:+SET (${#NOTION_TOKEN} chars)}"
TOKEN_PREFIX="${NOTION_TOKEN:0:4}"
if [ -n "$NOTION_TOKEN" ] && [ "$TOKEN_PREFIX" != "ntn_" ]; then
  echo "WARNING: Token does not start with 'ntn_' — may be using legacy format"
fi

# 3. API connectivity — /v1/users/me as health check
# Notion-Version 2022-06-28 is the current stable REST API version.
echo -e "\n--- API Connectivity ---"
RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
  https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
LATENCY=$(echo "$RESPONSE" | tail -2 | head -1)
BODY=$(echo "$RESPONSE" | head -n -2)

echo "HTTP Status: $HTTP_CODE"
echo "Latency: ${LATENCY}s"

if [ "$HTTP_CODE" = "200" ]; then
  echo "Bot Name: $(echo "$BODY" | jq -r '.name // "unknown"')"
  echo "Bot Type: $(echo "$BODY" | jq -r '.type // "unknown"')"
else
  echo "Error Code: $(echo "$BODY" | jq -r '.code // "unknown"')"
  echo "Message: $(echo "$BODY" | jq -r '.message // "unknown"')"
fi

# 4. Notion platform status
echo -e "\n--- Notion Platform Status ---"
curl -s https://status.notion.so/api/v2/status.json \
  | jq -r '.status.description // "Could not reach status page"' 2>/dev/null \
  || echo "Could not reach status.notion.so"

# 5. Rate limit baseline (3 req/sec across all endpoints)
echo -e "\n--- Rate Limit Info ---"
echo "Notion enforces 3 requests/second per integration (across all endpoints)"
echo "Average request rate limits are not exposed in response headers"
```

### Step 2: Full Debug Bundle Script

When the quick check is not enough, run the full collector. It writes an
environment snapshot, the redacted auth/database/platform JSON, redacted
application logs, the npm dependency tree, and a redacted `.env` copy into a
timestamped directory, then tars it up as `notion-debug-YYYYMMDD-HHMMSS.tar.gz`.
It is safe to attach to a support ticket — tokens, secrets, and avatars are
stripped before packaging.

See the complete collector script (`notion-debug-bundle.sh`) in
[full implementation](references/implementation.md).

### Step 3: Programmatic Diagnostics

For structured diagnostics inside a Node/TypeScript app, use the SDK directly to
test auth (`/v1/users/me`), database retrieval, and workspace-level search. It
returns a plain object for logging or serialization and maps
`APIErrorCode.ObjectNotFound` to the actionable "integration not invited" hint.

See the full `collectNotionDiagnostics()` function in
[the programmatic diagnostics reference](references/implementation.md).

## Output

- `notion-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `environment.txt` — SDK version, Node version, token prefix, OS
  - `api-auth.json` — Bot user info from `/v1/users/me` (avatar redacted)
  - `database-access.json` — Database retrieve result (if `NOTION_DATABASE_ID` set)
  - `platform-status.json` — status.notion.so health and active incidents
  - `logs-*-redacted.txt` — Recent Notion-related log entries (tokens masked)
  - `dependency-tree.txt` — Full npm dependency tree for `@notionhq/client`
  - `env-redacted.txt` — Environment config (all values masked)

## Error Handling

| Error | HTTP | Cause | Fix |
| ------- | ------ | ------- | ----- |
| `unauthorized` | 401 | Invalid or missing token | Verify `NOTION_TOKEN` starts with `ntn_`, regenerate in integration settings |
| `object_not_found` | 404 | Page/DB not shared with integration | Open page in Notion, click Share, invite the integration |
| `rate_limited` | 429 | Exceeded 3 req/sec | Add exponential backoff; batch requests where possible |
| `validation_error` | 400 | Malformed page/database ID | Use 32-char UUID format (with or without dashes) |
| `conflict_error` | 409 | Concurrent edit conflict | Retry with fresh data; avoid parallel writes to same block |
| `internal_server_error` | 500 | Notion platform issue | Check status.notion.so; retry after 60s |

## Examples

Quick reference for the recurring gotchas — validate a token prefix:

```bash
# Valid tokens start with ntn_; the old secret_* format is deprecated.
echo "Token prefix: ${NOTION_TOKEN:0:4}"
```

For page ID normalization (dashed vs dashless UUIDs) and the full redaction
rules (what to ALWAYS REDACT vs what is SAFE TO INCLUDE in a bundle), see
[examples and redaction rules](references/examples.md).

## Resources

- [Notion API Introduction](https://developers.notion.com/reference/intro) — authentication, versioning, pagination
- [Notion Status Page](https://status.notion.so) — real-time platform health
- [Notion Error Codes](https://developers.notion.com/reference/errors) — full error code reference
- [Integration Setup Guide](https://developers.notion.com/docs/create-a-notion-integration) — creating and configuring integrations
- [Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec limit details

## Next Steps

For rate limit issues, see `notion-rate-limits`. For page sharing and permission problems, see `notion-enterprise-rbac`.
