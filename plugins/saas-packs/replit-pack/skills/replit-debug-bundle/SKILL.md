---
name: replit-debug-bundle
description: |
  Collect Replit diagnostic info for debugging deployments, workspace issues, and support tickets.
  Use when encountering persistent issues, preparing support tickets,
  or collecting system state for troubleshooting Replit problems.
  Trigger with phrases like "replit debug", "replit support bundle",
  "collect replit logs", "replit diagnostic", "replit troubleshoot".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, debugging, support]

---
# Replit Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'Node: N/A'`
!`python3 --version 2>/dev/null || echo 'Python: N/A'`
!`echo "REPL_SLUG=$REPL_SLUG REPL_OWNER=$REPL_OWNER" 2>/dev/null || echo 'Not on Replit'`

## Overview
Collect all diagnostic information needed to debug Replit workspace, deployment, and database issues. Produces a redacted evidence bundle safe for sharing with Replit support.

## Prerequisites
- Shell access in Replit Workspace
- Permission to read logs and configuration
- Access to deployment monitoring (if deployed)

## Instructions

### Step 1: Automated Debug Bundle Script
```bash
#!/bin/bash
set -euo pipefail
# replit-debug-bundle.sh

BUNDLE="replit-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"/{env,db,config,network,packages}

echo "=== Replit Debug Bundle ===" > "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "" >> "$BUNDLE/summary.txt"

# 1. Environment info
echo "--- Runtime ---" >> "$BUNDLE/env/runtime.txt"
node --version >> "$BUNDLE/env/runtime.txt" 2>&1 || echo "Node: N/A" >> "$BUNDLE/env/runtime.txt"
python3 --version >> "$BUNDLE/env/runtime.txt" 2>&1 || echo "Python: N/A" >> "$BUNDLE/env/runtime.txt"
uname -a >> "$BUNDLE/env/runtime.txt"

# 2. Replit environment variables (safe ones only)
echo "--- Replit Env ---" >> "$BUNDLE/env/replit-vars.txt"
echo "REPL_SLUG=$REPL_SLUG" >> "$BUNDLE/env/replit-vars.txt"
echo "REPL_OWNER=$REPL_OWNER" >> "$BUNDLE/env/replit-vars.txt"
echo "REPL_ID=$REPL_ID" >> "$BUNDLE/env/replit-vars.txt"
echo "REPLIT_DB_URL=${REPLIT_DB_URL:+SET}" >> "$BUNDLE/env/replit-vars.txt"
echo "DATABASE_URL=${DATABASE_URL:+SET}" >> "$BUNDLE/env/replit-vars.txt"
echo "NODE_ENV=${NODE_ENV:-unset}" >> "$BUNDLE/env/replit-vars.txt"

# 3. Package versions
npm list --depth=0 > "$BUNDLE/packages/npm.txt" 2>&1 || true
pip list > "$BUNDLE/packages/pip.txt" 2>&1 || true

# 4. Configuration files (redacted)
cp .replit "$BUNDLE/config/.replit" 2>/dev/null || echo "No .replit" > "$BUNDLE/config/.replit"
cp replit.nix "$BUNDLE/config/replit.nix" 2>/dev/null || echo "No replit.nix" > "$BUNDLE/config/replit.nix"

# 5. Database connectivity
echo "--- Database ---" >> "$BUNDLE/db/status.txt"
if [ -n "${DATABASE_URL:-}" ]; then
  echo "PostgreSQL: configured" >> "$BUNDLE/db/status.txt"
  # Test connection without exposing credentials
  node -e "const {Pool}=require('pg');const p=new Pool({connectionString:process.env.DATABASE_URL,ssl:{rejectUnauthorized:false}});p.query('SELECT 1').then(()=>console.log('Connected')).catch(e=>console.log('Failed:',e.message)).finally(()=>p.end())" >> "$BUNDLE/db/status.txt" 2>&1 || echo "pg not installed" >> "$BUNDLE/db/status.txt"
fi
if [ -n "${REPLIT_DB_URL:-}" ]; then
  echo "Replit KV DB: configured" >> "$BUNDLE/db/status.txt"
  curl -s "$REPLIT_DB_URL?prefix=" | head -20 >> "$BUNDLE/db/kv-keys.txt" 2>/dev/null || echo "KV DB unreachable" >> "$BUNDLE/db/status.txt"
fi

# 6. Network connectivity
echo "--- Network ---" >> "$BUNDLE/network/connectivity.txt"
curl -s -o /dev/null -w "replit.com: HTTP %{http_code} (%{time_total}s)\n" https://replit.com >> "$BUNDLE/network/connectivity.txt"
curl -s -o /dev/null -w "status.replit.com: HTTP %{http_code} (%{time_total}s)\n" https://status.replit.com >> "$BUNDLE/network/connectivity.txt"

# 7. Disk usage
df -h / > "$BUNDLE/env/disk.txt" 2>/dev/null
du -sh . >> "$BUNDLE/env/disk.txt" 2>/dev/null

# 8. Process state
ps aux | head -20 > "$BUNDLE/env/processes.txt" 2>/dev/null

# Package bundle
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo ""
echo "Debug bundle created: $BUNDLE.tar.gz"
echo "Size: $(du -h "$BUNDLE.tar.gz" | cut -f1)"
rm -rf "$BUNDLE"
```

### Step 2: Quick Health Check
```bash
set -euo pipefail
# Fast triage without full bundle
echo "=== Quick Replit Health Check ==="
echo "Repl: $REPL_SLUG (owner: $REPL_OWNER)"
echo "Node: $(node --version 2>/dev/null || echo N/A)"
echo "Python: $(python3 --version 2>/dev/null || echo N/A)"
echo "DB URL: ${DATABASE_URL:+configured}"
echo "KV URL: ${REPLIT_DB_URL:+configured}"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
curl -s -o /dev/null -w "Replit.com: %{http_code}\n" https://replit.com
curl -s https://status.replit.com/api/v2/summary.json 2>/dev/null | \
  python3 -c "import sys,json;d=json.load(sys.stdin);print('Status:', d['status']['description'])" 2>/dev/null || echo "Status: check https://status.replit.com"
```

### Step 3: Deployment-Specific Diagnostics
```bash
set -euo pipefail
# Check deployment health
DEPLOY_URL="https://your-app.replit.app"  # Replace with your URL

echo "=== Deployment Diagnostics ==="
curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" "$DEPLOY_URL/health"

# Check response headers
curl -sI "$DEPLOY_URL" | grep -iE "^(server|x-replit|content-type|cache)"

# Measure cold start (if autoscale)
echo "Cold start test (wait 5 min for sleep, then):"
echo "time curl -s $DEPLOY_URL/health"
```

## Sensitive Data Handling
**ALWAYS REDACT before sharing:**
- API keys, tokens, passwords
- DATABASE_URL connection strings
- PII (emails, names, IDs)
- REPL_IDENTITY tokens

**Safe to include:**
- Error messages and stack traces
- Package versions
- `.replit` and `replit.nix` contents
- HTTP status codes and response times

## Error Handling
| Item | Purpose | Safe to Share |
|------|---------|---------------|
| Runtime versions | Compatibility check | Yes |
| Replit env vars (names only) | Configuration status | Yes |
| Package list | Dependency conflicts | Yes |
| Network latency | Connectivity issues | Yes |
| Disk usage | Storage problems | Yes |
| Connection strings | Database access | NEVER |

## Submit to Support
1. Create bundle: `bash replit-debug-bundle.sh`
2. Review for sensitive data
3. Open support ticket at https://replit.com/support
4. Attach the `.tar.gz` bundle
5. Include: steps to reproduce, expected vs actual behavior

## Resources
- [Replit Support](https://replit.com/support)
- [Replit Status Page](https://status.replit.com)
- [Replit Community Forum](https://ask.replit.com)

## Next Steps
For rate limit issues, see `replit-rate-limits`.
