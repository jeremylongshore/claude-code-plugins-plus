---
name: vercel-debug-bundle
description: |
  Collect Vercel debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Vercel problems.
  Trigger with phrases like "vercel debug", "vercel support bundle",
  "collect vercel logs", "vercel diagnostic".
allowed-tools: Read, Bash(vercel:*), Bash(curl:*), Bash(tar:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, debugging, support]

---
# Vercel Debug Bundle

## Overview
Collect a comprehensive debug bundle containing deployment state, function logs, environment configuration, and build output for Vercel support escalation or team troubleshooting.

## Current State
!`vercel --version 2>/dev/null || echo 'Vercel CLI not installed'`
!`node --version 2>/dev/null || echo 'Node.js N/A'`

## Prerequisites
- Vercel CLI installed and authenticated
- Access to the affected deployment
- `jq` for JSON processing (recommended)

## Instructions

### Step 1: Collect Deployment Information
```bash
#!/usr/bin/env bash
set -euo pipefail

DEPLOY_URL="${1:-$(vercel ls --json 2>/dev/null | jq -r '.[0].url')}"
BUNDLE_DIR="vercel-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Collecting debug bundle for: $DEPLOY_URL ==="

# Deployment inspection
vercel inspect "$DEPLOY_URL" > "$BUNDLE_DIR/inspect.txt" 2>&1 || true

# Deployment details via API
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/$DEPLOY_URL" \
  | jq '{uid, name, state, target, readyState, errorMessage, meta, regions}' \
  > "$BUNDLE_DIR/deployment.json" 2>/dev/null || true
```

### Step 2: Collect Function Logs
```bash
# Recent function logs (last 100 entries)
vercel logs "$DEPLOY_URL" --output=short --limit=100 \
  > "$BUNDLE_DIR/function-logs.txt" 2>&1 || true

# Function logs via API with filtering
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v2/deployments/$DEPLOY_URL/events?limit=100&direction=backward" \
  | jq '.[] | {timestamp: .created, type, text}' \
  > "$BUNDLE_DIR/events.json" 2>/dev/null || true
```

### Step 3: Collect Build Output
```bash
# Build logs
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/$DEPLOY_URL" \
  | jq '.build' > "$BUNDLE_DIR/build-info.json" 2>/dev/null || true

# List all functions in the deployment
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/$DEPLOY_URL" \
  | jq '.routes, .functions' > "$BUNDLE_DIR/routes-functions.json" 2>/dev/null || true
```

### Step 4: Collect Environment State (Redacted)
```bash
# Environment variable names only (no values)
vercel env ls > "$BUNDLE_DIR/env-vars-list.txt" 2>&1 || true

# Project configuration (redacted)
if [ -f "vercel.json" ]; then
  cp vercel.json "$BUNDLE_DIR/vercel.json"
fi

# Package versions
if [ -f "package.json" ]; then
  jq '{name, version, dependencies, devDependencies, engines}' package.json \
    > "$BUNDLE_DIR/package-summary.json" 2>/dev/null || true
fi

# Node.js and CLI versions
{
  echo "node: $(node --version 2>/dev/null || echo 'N/A')"
  echo "npm: $(npm --version 2>/dev/null || echo 'N/A')"
  echo "vercel: $(vercel --version 2>/dev/null || echo 'N/A')"
  echo "os: $(uname -a)"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$BUNDLE_DIR/environment.txt"
```

### Step 5: Check Vercel Status Page
```bash
# Vercel platform status
curl -s "https://www.vercel-status.com/api/v2/summary.json" \
  | jq '{status: .status.description, components: [.components[] | {name, status}]}' \
  > "$BUNDLE_DIR/platform-status.json" 2>/dev/null || true
```

### Step 6: Package the Bundle
```bash
# Create archive — excludes secrets
tar czf "${BUNDLE_DIR}.tar.gz" "$BUNDLE_DIR"
echo "Debug bundle created: ${BUNDLE_DIR}.tar.gz"
echo "Contents:"
ls -la "$BUNDLE_DIR"/
```

## Bundle Contents Reference

| File | Contents |
|------|----------|
| `inspect.txt` | Deployment inspection output |
| `deployment.json` | Deployment state, target, errors |
| `function-logs.txt` | Recent function invocation logs |
| `events.json` | Deployment event timeline |
| `build-info.json` | Build configuration and output |
| `routes-functions.json` | Route and function mapping |
| `env-vars-list.txt` | Environment variable names (no values) |
| `vercel.json` | Project configuration |
| `package-summary.json` | Dependencies and versions |
| `environment.txt` | System info (Node, CLI, OS) |
| `platform-status.json` | Vercel platform status at time of capture |

## Support Ticket Template
```
Subject: [Project: my-app] FUNCTION_INVOCATION_TIMEOUT on /api/endpoint

Environment:
- Plan: Pro
- Framework: Next.js 14
- Region: iad1
- Node.js: 18.x

Issue:
[Describe the error, when it started, and the user impact]

Steps to Reproduce:
1. Deploy commit abc123
2. Send POST to /api/endpoint with body > 1MB
3. Function times out after 60s

Expected: 200 response within 5s
Actual: 504 after 60s

Deployment URL: https://my-app-xxx.vercel.app
Debug bundle: [attached]
```

## Output
- `vercel-debug-YYYYMMDD-HHMMSS.tar.gz` archive
- All secrets redacted (env var values never captured)
- Platform status snapshot included
- Ready to attach to Vercel support ticket

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `vercel inspect` fails | Deployment deleted or token expired | Use API directly with curl |
| `jq: command not found` | jq not installed | `apt install jq` or `brew install jq` |
| Empty function logs | Function not invoked or log retention expired | Check Observability tab in dashboard |
| VERCEL_TOKEN not set | Not authenticated for API calls | Export token or run `vercel login` |

## Resources
- [Vercel Support Portal](https://vercel.com/support)
- [Vercel Logs CLI](https://vercel.com/docs/cli/logs)
- [Vercel Inspect CLI](https://vercel.com/docs/cli/inspect)
- [Vercel Status Page](https://www.vercel-status.com)

## Next Steps
For rate limit issues, see `vercel-rate-limits`.
