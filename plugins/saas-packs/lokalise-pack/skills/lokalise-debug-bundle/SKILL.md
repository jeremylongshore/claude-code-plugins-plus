---
name: lokalise-debug-bundle
description: |
  Collect Lokalise debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Lokalise problems.
  Trigger with phrases like "lokalise debug", "lokalise support bundle",
  "collect lokalise logs", "lokalise diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(lokalise2:*), Bash(node:*), Bash(npm:*), Bash(jq:*), Bash(sed:*), Bash(mkdir:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

Collect all diagnostic information needed to troubleshoot Lokalise integration issues or file a support ticket — environment versions, SDK/CLI status, API connectivity, project listings with key counts, upload process status, and redacted logs, bundled into a timestamped `.tar.gz` archive.

## Prerequisites

- `LOKALISE_API_TOKEN` environment variable set (or token available to provide)
- `curl` and `jq` available on PATH
- Optional: `@lokalise/node-api` SDK installed in current project
- Optional: `lokalise2` CLI installed

## Instructions

### Step 1: Create the Bundle Directory

```bash
set -euo pipefail
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BUNDLE_DIR="lokalise-debug-${TIMESTAMP}"
mkdir -p "${BUNDLE_DIR}"
echo "Bundle directory: ${BUNDLE_DIR}"
```

### Step 2: Collect Environment Information

```bash
set -euo pipefail
cat > "${BUNDLE_DIR}/environment.txt" <<ENVEOF
=== System ===
OS: $(uname -srm)
Shell: ${SHELL:-unknown}
Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

=== Runtime Versions ===
Node.js: $(node --version 2>/dev/null || echo 'not installed')
npm: $(npm --version 2>/dev/null || echo 'not installed')
Python: $(python3 --version 2>/dev/null || echo 'not installed')

=== Lokalise SDK ===
$(npm list @lokalise/node-api 2>/dev/null || echo 'SDK not found in project')

=== Lokalise CLI ===
$(lokalise2 --version 2>/dev/null || echo 'CLI not installed')

=== Token Status ===
LOKALISE_API_TOKEN: $([ -n "${LOKALISE_API_TOKEN:-}" ] && echo "SET (${#LOKALISE_API_TOKEN} chars)" || echo "NOT SET")
ENVEOF
echo "Environment info collected."
```

### Step 3: Test API Connectivity

```bash
set -euo pipefail
echo "=== API Connectivity Test ===" > "${BUNDLE_DIR}/api-connectivity.txt"

# Test DNS resolution
echo -e "\n--- DNS Resolution ---" >> "${BUNDLE_DIR}/api-connectivity.txt"
nslookup api.lokalise.com 2>&1 | tail -4 >> "${BUNDLE_DIR}/api-connectivity.txt" || echo "nslookup failed" >> "${BUNDLE_DIR}/api-connectivity.txt"

# Test HTTPS connectivity and response time
echo -e "\n--- HTTPS Connectivity ---" >> "${BUNDLE_DIR}/api-connectivity.txt"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\nConnect Time: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal Time: %{time_total}s\nRemote IP: %{remote_ip}\n" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/system/languages?limit=1" \
  >> "${BUNDLE_DIR}/api-connectivity.txt" 2>&1

# Check rate limit headers
echo -e "\n--- Rate Limit Headers ---" >> "${BUNDLE_DIR}/api-connectivity.txt"
curl -s -D - -o /dev/null \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/system/languages?limit=1" 2>/dev/null \
  | grep -iE '(x-ratelimit|retry-after)' >> "${BUNDLE_DIR}/api-connectivity.txt" || echo "No rate limit headers found" >> "${BUNDLE_DIR}/api-connectivity.txt"

echo "API connectivity tested."
```

### Step 4: List Projects and Key Counts

```bash
set -euo pipefail
echo "Fetching project list..."

curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects?limit=100&include_statistics=1" \
  | jq '[.projects[] | {
    project_id: .project_id,
    name: .name,
    base_language: .base_language_iso,
    keys: .statistics.keys_total,
    languages: (.statistics.languages // [] | length),
    progress: .statistics.progress_total,
    created: .created_at
  }]' > "${BUNDLE_DIR}/projects.json" 2>/dev/null || echo '{"error": "Failed to fetch projects"}' > "${BUNDLE_DIR}/projects.json"

# Summary line
PROJ_COUNT=$(jq 'length' "${BUNDLE_DIR}/projects.json" 2>/dev/null || echo "0")
TOTAL_KEYS=$(jq '[.[].keys // 0] | add // 0' "${BUNDLE_DIR}/projects.json" 2>/dev/null || echo "0")
echo "Found ${PROJ_COUNT} projects with ${TOTAL_KEYS} total keys."
```

### Step 5: Check File Upload Process Status

```bash
set -euo pipefail
# Check queued processes for each project (file uploads are async)
echo "[]" > "${BUNDLE_DIR}/processes.json"

for PID in $(jq -r '.[].project_id' "${BUNDLE_DIR}/projects.json" 2>/dev/null); do
  curl -s -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
    "https://api.lokalise.com/api2/projects/${PID}/processes?limit=10" \
    | jq --arg pid "$PID" '[.processes[]? | {project_id: $pid, type: .type, status: .status, created_at: .created_at, message: .message}]' \
    >> "${BUNDLE_DIR}/processes-raw.json" 2>/dev/null || true
  sleep 0.17  # Respect 6 req/s rate limit
done

# Merge all process entries
jq -s 'flatten' "${BUNDLE_DIR}/processes-raw.json" > "${BUNDLE_DIR}/processes.json" 2>/dev/null || true
rm -f "${BUNDLE_DIR}/processes-raw.json"

PROC_COUNT=$(jq 'length' "${BUNDLE_DIR}/processes.json" 2>/dev/null || echo "0")
echo "Found ${PROC_COUNT} recent upload processes."
```

### Step 6: Collect and Redact Application Logs

```bash
set -euo pipefail
# Gather any lokalise-related log lines from common locations
{
  echo "=== npm debug log (if exists) ==="
  cat ~/.npm/_logs/*-debug.log 2>/dev/null | grep -i lokalise | tail -50 || echo "No npm debug logs"

  echo -e "\n=== Application stderr/stdout (recent) ==="
  grep -ri "lokalise" /tmp/*.log 2>/dev/null | tail -30 || echo "No /tmp logs found"
} > "${BUNDLE_DIR}/logs-raw.txt" 2>/dev/null || true

# Redact sensitive values
sed -E \
  -e 's/([0-9a-f]{32,})/[REDACTED_TOKEN]/gi' \
  -e 's/(X-Api-Token:\s*)[^ ]*/\1[REDACTED]/gi' \
  -e 's/(apiKey:\s*["'"'"']?)[^"'"'"',]+/\1[REDACTED]/gi' \
  -e 's/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[REDACTED_EMAIL]/g' \
  "${BUNDLE_DIR}/logs-raw.txt" > "${BUNDLE_DIR}/logs-redacted.txt" 2>/dev/null || true
rm -f "${BUNDLE_DIR}/logs-raw.txt"
echo "Logs collected and redacted."
```

### Step 7: Create the tar.gz Bundle

```bash
set -euo pipefail
tar -czf "${BUNDLE_DIR}.tar.gz" "${BUNDLE_DIR}/"
SIZE=$(du -h "${BUNDLE_DIR}.tar.gz" | cut -f1)
echo "Bundle created: ${BUNDLE_DIR}.tar.gz (${SIZE})"
echo "Contents:"
tar -tzf "${BUNDLE_DIR}.tar.gz"
```

## Output

- `lokalise-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `environment.txt` — Node.js, SDK, CLI versions, token status
  - `api-connectivity.txt` — DNS, HTTPS latency, rate limit headers
  - `projects.json` — Project list with key/language counts and progress
  - `processes.json` — Recent file upload process statuses per project
  - `logs-redacted.txt` — Relevant logs with tokens and emails scrubbed

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Token invalid or expired | Regenerate token in Lokalise > User Profile > API Tokens |
| `403 Forbidden` | Token lacks read scope | Use a read-write token or admin token |
| `429 Too Many Requests` | Rate limit exceeded during project scan | Script includes `sleep 0.17` between calls; reduce `--limit` if still hitting |
| Empty `projects.json` | Token has no project access | Verify the token owner is a contributor on at least one project |
| `nslookup` fails | DNS resolution blocked | Try `dig api.lokalise.com` or check `/etc/resolv.conf` |
| `tar` permission denied | Bundle dir in read-only location | Run from a writable directory like `~/tmp` |

## Examples

### Quick One-Liner API Health Check

```bash
set -euo pipefail
curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects?limit=1" | jq '{project: .projects[0].name, keys: .projects[0].statistics.keys_total}'
```

### Check SDK Version Programmatically

```bash
set -euo pipefail
node -e "const pkg = require('@lokalise/node-api/package.json'); console.log('SDK:', pkg.version, '| Node:', process.version)"
```

### Redaction Safety Checklist

**Always redacted:** API tokens, webhook secrets, OAuth credentials, email addresses, any 32+ character hex strings.

**Safe to include:** Error messages, stack traces (after redaction pass), SDK and runtime versions, project IDs, HTTP status codes, rate limit header values.

## Resources

- [Lokalise API Reference](https://developers.lokalise.com/reference)
- [Lokalise Status Page](https://status.lokalise.com)
- [Lokalise Support](mailto:support@lokalise.com)
- [Community Forum](https://community.lokalise.com)
- [Rate Limits Documentation](https://developers.lokalise.com/docs/api-rate-limits)

## Next Steps

- For rate limit issues found in the bundle, see `lokalise-performance-tuning`.
- For SDK version mismatches, see `lokalise-upgrade-migration`.
- Attach the `.tar.gz` bundle directly to a Lokalise support ticket at support@lokalise.com.
