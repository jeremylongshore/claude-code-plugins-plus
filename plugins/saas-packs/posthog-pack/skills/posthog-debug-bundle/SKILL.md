---
name: posthog-debug-bundle
description: |
  Collect PostHog debug evidence for support tickets and troubleshooting.
  Gathers SDK versions, API connectivity, event flow status, flag definitions,
  and redacted configuration into a support-ready archive.
  Trigger: "posthog debug", "posthog support bundle", "collect posthog logs",
  "posthog diagnostic", "posthog not working debug".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, debugging]
---

# PostHog Debug Bundle

## Current State

!`node --version 2>/dev/null || echo 'N/A'`
!`npm list posthog-js posthog-node 2>/dev/null | grep posthog || echo 'No PostHog SDK found'`

## Overview

Collect diagnostic evidence for PostHog support tickets. Gathers SDK versions, API connectivity, feature flag status, event flow verification, and redacted configuration. All secrets are automatically redacted.

## Prerequisites

- PostHog SDK installed in project
- Access to environment variables
- `curl` and `jq` available

## Instructions

### Step 1: Run Full Diagnostic Script

```bash
#!/bin/bash
set -euo pipefail

BUNDLE_DIR="posthog-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== PostHog Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- Environment ---
echo "--- Runtime Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not found')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not found')" >> "$BUNDLE_DIR/summary.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'not found')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -srm)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- SDK Versions ---
echo "--- PostHog SDK Versions ---" >> "$BUNDLE_DIR/summary.txt"
npm list posthog-js posthog-node 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "No npm PostHog packages" >> "$BUNDLE_DIR/summary.txt"
pip3 show posthog 2>/dev/null | grep -E "Name|Version" >> "$BUNDLE_DIR/summary.txt" || true
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- API Connectivity ---
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "US Cloud ingest: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" https://us.i.posthog.com/healthz >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "" >> "$BUNDLE_DIR/summary.txt"
echo -n "EU Cloud ingest: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" https://eu.i.posthog.com/healthz >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "" >> "$BUNDLE_DIR/summary.txt"
echo -n "App API: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" https://app.posthog.com/api/ >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- Environment Variables (redacted) ---
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Environment Variables (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
env | grep -i posthog | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "No POSTHOG env vars found" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- Key Type Detection ---
echo "--- API Key Types ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${NEXT_PUBLIC_POSTHOG_KEY:-}" ]; then
  echo "Project key prefix: $(echo "$NEXT_PUBLIC_POSTHOG_KEY" | head -c 4)_..." >> "$BUNDLE_DIR/summary.txt"
fi
if [ -n "${POSTHOG_PERSONAL_API_KEY:-}" ]; then
  echo "Personal key prefix: $(echo "$POSTHOG_PERSONAL_API_KEY" | head -c 4)_..." >> "$BUNDLE_DIR/summary.txt"
fi

echo "" >> "$BUNDLE_DIR/summary.txt"
echo "Bundle complete: $BUNDLE_DIR/" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Test Event Capture Flow

```bash
set -euo pipefail
# Send a test event and verify it was accepted
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d "{
    \"api_key\": \"${NEXT_PUBLIC_POSTHOG_KEY}\",
    \"event\": \"debug_bundle_test\",
    \"distinct_id\": \"debug-$(date +%s)\",
    \"properties\": {\"test\": true}
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

echo "Capture test: HTTP $HTTP_CODE"
echo "Response: $BODY"

# Expected: HTTP 200, Response: {"status": 1}
```

### Step 3: Check Feature Flag Status

```bash
set -euo pipefail
# Evaluate flags via the /decide endpoint
curl -s -X POST 'https://us.i.posthog.com/decide/?v=3' \
  -H 'Content-Type: application/json' \
  -d "{
    \"api_key\": \"${NEXT_PUBLIC_POSTHOG_KEY}\",
    \"distinct_id\": \"debug-test\"
  }" | jq '{
    featureFlags: .featureFlags,
    errorsWhileComputingFlags: .errorsWhileComputingFlags,
    sessionRecording: (.sessionRecording != false)
  }'
```

### Step 4: Verify Admin API Access

```bash
set -euo pipefail
# Test personal API key (if available)
if [ -n "${POSTHOG_PERSONAL_API_KEY:-}" ]; then
  curl -s "https://app.posthog.com/api/projects/" \
    -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | \
    jq '[.[] | {id, name, created_at}]' > "$BUNDLE_DIR/projects.json" 2>/dev/null || \
    echo "Personal API key failed" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 5: Package and Review

```bash
set -euo pipefail
# Review for any accidentally included secrets
grep -rn "phc_\|phx_\|Bearer " "$BUNDLE_DIR/" | grep -v REDACTED | grep -v "prefix:" && \
  echo "WARNING: Potential secret found — review before sharing" || \
  echo "No secrets detected in bundle"

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz ($(du -h "$BUNDLE_DIR.tar.gz" | cut -f1))"
```

## Checklist

| Item | Collected | Purpose |
|------|-----------|---------|
| Node/Python versions | Yes | SDK compatibility |
| PostHog SDK versions | Yes | Version-specific bugs |
| API connectivity | Yes | Network/firewall issues |
| Event capture test | Yes | End-to-end verification |
| Feature flag status | Yes | Flag evaluation issues |
| Environment vars (redacted) | Yes | Configuration problems |
| Key type detection | Yes | Wrong key type errors |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| All connectivity fails | Corporate firewall | Check proxy settings, try VPN |
| Capture returns non-200 | Invalid API key | Verify `phc_` key in project settings |
| `/decide` fails | Key/host mismatch | Ensure key matches the host region |
| Personal API 401 | Expired key | Regenerate in Settings > Personal API Keys |

## Output

- `posthog-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` — Runtime, SDK versions, connectivity, redacted config
  - `projects.json` — Project list (if personal key available)
  - Test event capture and flag evaluation results

## Resources

- [PostHog Status Page](https://status.posthog.com)
- [PostHog Support](https://posthog.com/docs/support)
- [PostHog API Overview](https://posthog.com/docs/api)

## Next Steps

For rate limit issues, see `posthog-rate-limits`.
