---
name: mindtickle-debug-bundle
description: |
  Debug Bundle for MindTickle.
  Trigger: "mindtickle debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Debug Bundle

## Overview

This debug bundle collects diagnostic evidence from MindTickle sales enablement API
integrations for troubleshooting course delivery, quiz scoring, user progress tracking,
and CRM sync pipelines. It captures API token validation, course catalog accessibility,
user enrollment status, content module health, and Salesforce integration state. The
resulting tarball provides the evidence needed to diagnose training completion gaps,
broken content assignments, scoring discrepancies, and SSO provisioning failures
without requiring MindTickle admin panel access.

## Prerequisites

- `curl`, `jq`, `tar` installed
- `MINDTICKLE_API_KEY` set (API token from MindTickle Admin > Integrations > API)
- `MINDTICKLE_INSTANCE` set to your instance URL (e.g., `yourcompany.mindtickle.com`)

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-mindtickle-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "API Key: ${MINDTICKLE_API_KEY:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Instance: ${MINDTICKLE_INSTANCE:-NOT SET}" >> "$BUNDLE/environment.txt"
echo "Node: $(node -v 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# API connectivity — company info
echo "=== API Health ===" > "$BUNDLE/api-health.txt"
curl -sf -o "$BUNDLE/api-health.txt" -w "HTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer ${MINDTICKLE_API_KEY}" \
  "https://${MINDTICKLE_INSTANCE}/api/v2/company" 2>&1 || echo "UNREACHABLE" > "$BUNDLE/api-health.txt"

# Course catalog
echo "=== Courses ===" > "$BUNDLE/courses.json"
curl -sf -H "Authorization: Bearer ${MINDTICKLE_API_KEY}" \
  "https://${MINDTICKLE_INSTANCE}/api/v2/series?limit=10" \
  >> "$BUNDLE/courses.json" 2>&1 || echo '{"error":"FAILED"}' > "$BUNDLE/courses.json"

# User enrollment sample
echo "=== Users ===" > "$BUNDLE/users.json"
curl -sf -H "Authorization: Bearer ${MINDTICKLE_API_KEY}" \
  "https://${MINDTICKLE_INSTANCE}/api/v2/users?limit=5" \
  >> "$BUNDLE/users.json" 2>&1 || echo '{"error":"FAILED"}' > "$BUNDLE/users.json"

# Quiz/assessment results
echo "=== Assessments ===" > "$BUNDLE/assessments.json"
SERIES_ID=$(jq -r '.series[0].id // empty' "$BUNDLE/courses.json" 2>/dev/null)
if [ -n "${SERIES_ID:-}" ]; then
  curl -sf -H "Authorization: Bearer ${MINDTICKLE_API_KEY}" \
    "https://${MINDTICKLE_INSTANCE}/api/v2/series/${SERIES_ID}/progress?limit=5" \
    >> "$BUNDLE/assessments.json" 2>&1 || echo '{"error":"PROGRESS_FAILED"}' > "$BUNDLE/assessments.json"
else
  echo '{"error":"No courses found"}' > "$BUNDLE/assessments.json"
fi

# Recent logs
echo "=== Recent Logs ===" > "$BUNDLE/app-logs.txt"
tail -100 /var/log/mindtickle-sync/*.log >> "$BUNDLE/app-logs.txt" 2>/dev/null || echo "No sync logs found" >> "$BUNDLE/app-logs.txt"

# Rate limit status
echo "=== Rate Limits ===" > "$BUNDLE/rate-limits.txt"
curl -sI -H "Authorization: Bearer ${MINDTICKLE_API_KEY}" \
  "https://${MINDTICKLE_INSTANCE}/api/v2/company" 2>/dev/null | grep -i "x-rate\|retry-after\|x-ratelimit" >> "$BUNDLE/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE/rate-limits.txt"

# Package versions
echo "=== Dependencies ===" > "$BUNDLE/deps.txt"
npm ls 2>/dev/null | grep -i mindtickle >> "$BUNDLE/deps.txt" || echo "No MindTickle npm packages found" >> "$BUNDLE/deps.txt"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-mindtickle-*.tar.gz
cat debug-mindtickle-*/environment.txt           # Verify API key and instance
cat debug-mindtickle-*/api-health.txt            # Check HTTP status and latency
jq '.series | length' debug-mindtickle-*/courses.json     # Count courses
jq '.users | length' debug-mindtickle-*/users.json        # Check user provisioning
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| 401 on all endpoints | `environment.txt` shows key NOT SET | Generate API token in MindTickle Admin > Integrations > API Access |
| 403 on user endpoints | `users.json` shows permission error | Token missing `users.read` scope; regenerate with admin role permissions |
| Course list empty | `courses.json` returns empty series array | Verify courses are published (draft courses excluded from API); check team filter |
| Progress shows 0% for enrolled users | `assessments.json` shows no completion data | Content modules may not have tracking enabled; check series settings in admin |
| CRM sync stale | App logs show Salesforce auth errors | Re-authorize Salesforce connection in MindTickle Admin > CRM Integration |
| SSO users not appearing | `users.json` missing expected users | Check SCIM provisioning logs; verify IdP group assignment includes MindTickle app |

## Automated Health Check

```typescript
async function checkMindTickleHealth(): Promise<{
  status: string;
  latencyMs: number;
  companyOk: boolean;
  courseCount: number;
  userProvisioningOk: boolean;
}> {
  const apiKey = process.env.MINDTICKLE_API_KEY;
  const instance = process.env.MINDTICKLE_INSTANCE;
  const headers = { Authorization: `Bearer ${apiKey}` };
  const start = Date.now();

  const companyRes = await fetch(`https://${instance}/api/v2/company`, { headers });
  const coursesRes = await fetch(`https://${instance}/api/v2/series?limit=1`, { headers });
  const usersRes = await fetch(`https://${instance}/api/v2/users?limit=1`, { headers });

  let courseCount = 0;
  if (coursesRes.ok) {
    const data = await coursesRes.json();
    courseCount = data.series?.length ?? 0;
  }

  return {
    status: companyRes.ok ? "healthy" : "degraded",
    latencyMs: Date.now() - start,
    companyOk: companyRes.ok,
    courseCount,
    userProvisioningOk: usersRes.ok,
  };
}
```

## Resources

- [MindTickle API Documentation](https://developers.mindtickle.com)
- [MindTickle Status Page](https://status.mindtickle.com)
- [MindTickle Integration Guide](https://www.mindtickle.com/platform/integrations/)

## Next Steps

See `mindtickle-rate-limits`.
