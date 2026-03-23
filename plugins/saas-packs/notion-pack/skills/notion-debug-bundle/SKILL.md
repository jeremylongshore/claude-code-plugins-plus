---
name: notion-debug-bundle
description: |
  Collect Notion API diagnostic info for troubleshooting and support tickets.
  Use when encountering persistent API issues, token/auth failures, page access
  problems, or preparing diagnostic bundles for Notion support.
  Trigger with phrases like "notion debug", "notion diagnostic", "notion support
  bundle", "collect notion logs", "notion troubleshoot".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
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

```bash
#!/bin/bash
# notion-debug-bundle.sh — collects all diagnostic artifacts into a tarball
BUNDLE="notion-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# --- Environment snapshot ---
cat > "$BUNDLE/environment.txt" << EOF
Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Node: $(node --version 2>/dev/null || echo "not found")
npm: $(npm --version 2>/dev/null || echo "not found")
SDK: $(npm ls @notionhq/client 2>/dev/null | grep notionhq || echo "not found")
NOTION_TOKEN: ${NOTION_TOKEN:+SET (prefix: ${NOTION_TOKEN:0:4})}
OS: $(uname -a)
EOF

# --- API auth response (avatar redacted) ---
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  | jq 'del(.avatar_url)' > "$BUNDLE/api-auth.json" 2>/dev/null

# --- Database access test (if DATABASE_ID is set) ---
if [ -n "$NOTION_DATABASE_ID" ]; then
  curl -s "https://api.notion.com/v1/databases/${NOTION_DATABASE_ID}" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28" \
    | jq '{id, title: .title[0].plain_text, is_inline, created_time, last_edited_time}' \
    > "$BUNDLE/database-access.json" 2>/dev/null
else
  echo "NOTION_DATABASE_ID not set — skipping database access test" > "$BUNDLE/database-access.json"
fi

# --- Platform status with active incidents ---
curl -s https://status.notion.so/api/v2/summary.json \
  | jq '{status: .status, incidents: [.incidents[] | {name, status, updated_at}]}' \
  > "$BUNDLE/platform-status.json" 2>/dev/null

# --- Application logs (redacted) ---
for LOG_FILE in app.log server.log output.log; do
  if [ -f "$LOG_FILE" ]; then
    grep -i "notion\|notionhq\|api\.notion" "$LOG_FILE" | tail -100 \
      | sed 's/ntn_[a-zA-Z0-9_]*/ntn_[REDACTED]/g' \
      | sed 's/secret_[a-zA-Z0-9_]*/secret_[REDACTED]/g' \
      > "$BUNDLE/logs-${LOG_FILE%.log}-redacted.txt"
  fi
done

# --- Dependency tree for notion packages ---
npm ls @notionhq/client --all 2>/dev/null > "$BUNDLE/dependency-tree.txt"

# --- .env redacted copy ---
if [ -f ".env" ]; then
  sed 's/=.*/=[REDACTED]/' .env > "$BUNDLE/env-redacted.txt"
fi

# --- Package and clean up ---
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
rm -rf "$BUNDLE"
echo "Bundle created: $BUNDLE.tar.gz"
```

### Step 3: Programmatic Diagnostics

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

async function collectNotionDiagnostics(databaseId?: string) {
  const notion = new Client({ auth: process.env.NOTION_TOKEN });
  const debug: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    sdk: '@notionhq/client',
    nodeVersion: process.version,
    tokenSet: !!process.env.NOTION_TOKEN,
    tokenPrefix: process.env.NOTION_TOKEN?.substring(0, 4) ?? 'unset',
  };

  // Test authentication — /v1/users/me
  try {
    const me = await notion.users.me({});
    debug.auth = { status: 'ok', botName: me.name, type: me.type };
  } catch (error) {
    if (isNotionClientError(error)) {
      debug.auth = { status: 'error', code: error.code, message: error.message };
    }
  }

  // Test database access (if ID provided)
  if (databaseId) {
    try {
      const db = await notion.databases.retrieve({ database_id: databaseId });
      debug.database = {
        status: 'ok',
        title: (db as any).title?.[0]?.plain_text ?? 'untitled',
        isInline: (db as any).is_inline,
      };
    } catch (error) {
      if (isNotionClientError(error)) {
        debug.database = { status: 'error', code: error.code, message: error.message };
        if (error.code === APIErrorCode.ObjectNotFound) {
          debug.database.hint = 'Integration may not be invited to this database — share it via the page menu';
        }
      }
    }
  }

  // Test search (verifies workspace-level access)
  try {
    const search = await notion.search({ page_size: 1 });
    debug.search = {
      status: 'ok',
      accessiblePages: search.results.length > 0,
      resultType: search.results[0]?.object ?? 'none',
    };
  } catch (error) {
    if (isNotionClientError(error)) {
      debug.search = { status: 'error', code: error.code };
    }
  }

  return debug;
}
```

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
|-------|------|-------|-----|
| `unauthorized` | 401 | Invalid or missing token | Verify `NOTION_TOKEN` starts with `ntn_`, regenerate in integration settings |
| `object_not_found` | 404 | Page/DB not shared with integration | Open page in Notion, click Share, invite the integration |
| `rate_limited` | 429 | Exceeded 3 req/sec | Add exponential backoff; batch requests where possible |
| `validation_error` | 400 | Malformed page/database ID | Use 32-char UUID format (with or without dashes) |
| `conflict_error` | 409 | Concurrent edit conflict | Retry with fresh data; avoid parallel writes to same block |
| `internal_server_error` | 500 | Notion platform issue | Check status.notion.so; retry after 60s |

## Examples

### Token Format Validation
```bash
# Valid formats (all start with ntn_):
# ntn_abc123...  (internal integration token)
# Old format (secret_xyz...) is deprecated — regenerate in notion.so/my-integrations
echo "Token prefix: ${NOTION_TOKEN:0:4}"
```

### Page ID Normalization
```typescript
// Notion accepts both formats — but URLs use dashless form
const withDashes    = '12345678-1234-1234-1234-123456789abc';
const withoutDashes = '123456781234123412341234567890abc';

// The SDK handles both, but for consistency:
const normalized = rawId.replace(/-/g, '');
```

### Redaction Rules

**ALWAYS REDACT:** Integration tokens (`ntn_*`), OAuth client secrets, user emails, page content

**SAFE TO INCLUDE:** Error codes/messages, HTTP status codes, latencies, SDK versions, platform status, page/database IDs (non-sensitive metadata)

## Resources

- [Notion API Introduction](https://developers.notion.com/reference/intro) — authentication, versioning, pagination
- [Notion Status Page](https://status.notion.so) — real-time platform health
- [Notion Error Codes](https://developers.notion.com/reference/errors) — full error code reference
- [Integration Setup Guide](https://developers.notion.com/docs/create-a-notion-integration) — creating and configuring integrations
- [Rate Limits](https://developers.notion.com/reference/request-limits) — 3 req/sec limit details

## Next Steps

For rate limit issues, see `notion-rate-limits`. For page sharing and permission problems, see `notion-enterprise-rbac`.
