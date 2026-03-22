---
name: notion-debug-bundle
description: |
  Collect Notion API debug evidence for troubleshooting and support.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Notion problems.
  Trigger with phrases like "notion debug", "notion support bundle",
  "collect notion logs", "notion diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Debug Bundle

## Overview
Collect diagnostic information for Notion API issues: SDK version, connectivity, auth status, API version, and error logs.

## Prerequisites
- `@notionhq/client` installed
- `NOTION_TOKEN` configured
- Access to application logs

## Instructions

### Step 1: Quick Connectivity Check
```bash
#!/bin/bash
echo "=== Notion Debug Check ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. SDK version
echo -e "\n--- SDK Version ---"
npm list @notionhq/client 2>/dev/null || echo "SDK not found in node_modules"

# 2. Node version
echo -e "\n--- Runtime ---"
node --version
echo "NOTION_TOKEN: ${NOTION_TOKEN:+SET (${#NOTION_TOKEN} chars)}"

# 3. API connectivity (uses /v1/users/me as health check)
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
  echo "Bot Name: $(echo $BODY | jq -r '.name // "unknown"')"
  echo "Bot Type: $(echo $BODY | jq -r '.type // "unknown"')"
else
  echo "Error: $(echo $BODY | jq -r '.code // "unknown"')"
  echo "Message: $(echo $BODY | jq -r '.message // "unknown"')"
fi

# 4. Notion status page
echo -e "\n--- Notion Status ---"
curl -s https://status.notion.com/api/v2/status.json | jq -r '.status.description' 2>/dev/null || echo "Could not reach status page"
```

### Step 2: Full Debug Bundle Script
```bash
#!/bin/bash
# notion-debug-bundle.sh
BUNDLE="notion-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment info
cat > "$BUNDLE/environment.txt" << EOF
Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Node: $(node --version 2>/dev/null || echo "not found")
npm: $(npm --version 2>/dev/null || echo "not found")
SDK: $(npm list @notionhq/client 2>/dev/null | grep notionhq || echo "not found")
NOTION_TOKEN: ${NOTION_TOKEN:+SET}
OS: $(uname -a)
EOF

# API response (redacted)
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  | jq 'del(.avatar_url)' > "$BUNDLE/api-response.json" 2>/dev/null

# Notion platform status
curl -s https://status.notion.com/api/v2/summary.json \
  | jq '{status: .status, incidents: [.incidents[] | {name, status, updated_at}]}' \
  > "$BUNDLE/platform-status.json" 2>/dev/null

# Application logs (redacted — remove tokens)
if [ -f "app.log" ]; then
  grep -i "notion\|notionhq" app.log | tail -100 \
    | sed 's/ntn_[a-zA-Z0-9]*/ntn_[REDACTED]/g' \
    | sed 's/secret_[a-zA-Z0-9]*/secret_[REDACTED]/g' \
    > "$BUNDLE/app-logs-redacted.txt"
fi

# Package lock for dependency info
[ -f "package-lock.json" ] && jq '.packages | to_entries[] | select(.key | contains("notionhq"))' package-lock.json > "$BUNDLE/dependencies.json" 2>/dev/null

# Config (redacted)
if [ -f ".env" ]; then
  sed 's/=.*/=[REDACTED]/' .env > "$BUNDLE/env-redacted.txt"
fi

# Package
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
rm -rf "$BUNDLE"
echo "Bundle created: $BUNDLE.tar.gz"
```

### Step 3: Programmatic Debug Info
```typescript
import { Client, isNotionClientError } from '@notionhq/client';

async function collectDebugInfo() {
  const notion = new Client({ auth: process.env.NOTION_TOKEN });
  const debug: Record<string, any> = {
    timestamp: new Date().toISOString(),
    sdk: '@notionhq/client',
    nodeVersion: process.version,
    tokenSet: !!process.env.NOTION_TOKEN,
    tokenPrefix: process.env.NOTION_TOKEN?.substring(0, 4) ?? 'unset',
  };

  // Test authentication
  try {
    const me = await notion.users.me({});
    debug.auth = { status: 'ok', botName: me.name, type: me.type };
  } catch (error) {
    if (isNotionClientError(error)) {
      debug.auth = { status: 'error', code: error.code, message: error.message };
    }
  }

  // Test search (verifies workspace access)
  try {
    const search = await notion.search({ page_size: 1 });
    debug.search = { status: 'ok', hasResults: search.results.length > 0 };
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
  - `environment.txt` — SDK version, Node version, token status
  - `api-response.json` — Bot user info (avatar redacted)
  - `platform-status.json` — Notion service status
  - `app-logs-redacted.txt` — Recent Notion-related logs (tokens masked)
  - `env-redacted.txt` — Environment config (values masked)

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| SDK version | Version-specific issues | Yes |
| API response | Auth and connectivity | Yes |
| Platform status | Notion outage check | Yes |
| Error logs (redacted) | Root cause analysis | Yes |
| Config (redacted) | Configuration issues | Yes |

## Examples

### ALWAYS REDACT
- Integration secrets (`ntn_*`, `secret_*`)
- OAuth client secrets
- User PII (emails, names)

### Safe to Include
- Error codes and messages
- HTTP status codes and latencies
- SDK and runtime versions
- Notion platform status

## Resources
- [Notion Status Page](https://status.notion.com)
- [Notion API Introduction](https://developers.notion.com/reference/intro)

## Next Steps
For rate limit issues, see `notion-rate-limits`.
