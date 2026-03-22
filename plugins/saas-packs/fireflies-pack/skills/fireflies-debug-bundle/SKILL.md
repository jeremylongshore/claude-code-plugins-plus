---
name: fireflies-debug-bundle
description: |
  Collect Fireflies.ai debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Fireflies.ai problems.
  Trigger with phrases like "fireflies debug", "fireflies support bundle",
  "collect fireflies logs", "fireflies diagnostic".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, debugging]

---
# Fireflies.ai Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`

## Overview
Collect all diagnostic information needed to resolve Fireflies.ai integration issues. Generates a redacted bundle safe for sharing with support.

## Prerequisites
- `FIREFLIES_API_KEY` environment variable set
- `curl` and `jq` available
- Permission to collect environment info

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail

BUNDLE_DIR="fireflies-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Fireflies.ai Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# 1. Environment
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE_DIR/summary.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'N/A')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -s) $(uname -r)" >> "$BUNDLE_DIR/summary.txt"
echo "API Key: ${FIREFLIES_API_KEY:+SET (${#FIREFLIES_API_KEY} chars)}" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# 2. API Connectivity
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -o "$BUNDLE_DIR/api-response.json" -w "HTTP %{http_code} | %{time_total}s\n" \
  -X POST https://api.fireflies.ai/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ user { name email is_admin } }"}' \
  >> "$BUNDLE_DIR/summary.txt" 2>&1

# 3. User & Plan Info
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Account Info ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ user { name email is_admin num_transcripts minutes_consumed is_calendar_in_sync integrations } }"}' \
  | jq '.data.user | {name, is_admin, transcripts: .num_transcripts, minutes: .minutes_consumed, calendar_sync: .is_calendar_in_sync}' \
  >> "$BUNDLE_DIR/summary.txt" 2>/dev/null

# 4. Recent Transcripts (metadata only)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Recent Transcripts (last 5) ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ transcripts(limit: 5) { id title date duration organizer_email } }"}' \
  | jq '.data.transcripts[]? | {id, title, date, duration}' \
  >> "$BUNDLE_DIR/summary.txt" 2>/dev/null

# 5. GraphQL package versions
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Dependencies ---" >> "$BUNDLE_DIR/summary.txt"
npm list graphql graphql-request 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "No npm packages found" >> "$BUNDLE_DIR/summary.txt"
pip freeze 2>/dev/null | grep -i "request\|graphql" >> "$BUNDLE_DIR/summary.txt" || true

# 6. Config (redacted)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f .env ]; then
  cat .env | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"
fi

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

### Step 2: Quick Health Check
```bash
set -euo pipefail
echo "=== Fireflies Quick Health Check ==="

# Auth
echo -n "Auth: "
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { email } }"}' | jq -r '.data.user.email // .errors[0].message'

# Calendar sync
echo -n "Calendar: "
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ user { is_calendar_in_sync } }"}' | jq -r '.data.user.is_calendar_in_sync'

# Recent meeting
echo -n "Last meeting: "
curl -s -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ transcripts(limit: 1) { title date } }"}' | jq -r '.data.transcripts[0] | "\(.title) (\(.date))"'
```

## Sensitive Data Handling
**ALWAYS REDACT before sharing:**
- API keys and tokens
- Meeting content and transcripts
- Attendee emails and names
- PII in action items

**Safe to include:**
- Error codes and messages
- HTTP status codes and latency
- Package versions
- Account metadata (admin status, transcript count)

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| API connectivity | Is the endpoint reachable? | HTTP status + latency |
| Auth check | Is the API key valid? | User email or error code |
| Calendar sync | Is the bot getting invites? | Boolean sync status |
| Recent transcripts | Is processing working? | Metadata only (no content) |
| Dependencies | Version conflicts? | Package versions |

## Output
- `fireflies-debug-YYYYMMDD-HHMMSS.tar.gz` archive with:
  - `summary.txt` -- environment, connectivity, account info
  - `api-response.json` -- raw API response
  - `config-redacted.txt` -- configuration with secrets masked

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Fireflies Status](https://fireflies.ai)

## Next Steps
For rate limit issues, see `fireflies-rate-limits`.
