---
name: openevidence-debug-bundle
description: |
  Debug Bundle for OpenEvidence.
  Trigger: "openevidence debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Debug Bundle

## Overview

This debug bundle collects diagnostic evidence from OpenEvidence clinical decision support
API integrations for troubleshooting evidence retrieval, clinical query accuracy, and
response latency issues. It captures API token validation, clinical query endpoint health,
evidence citation availability, model version metadata, and response time benchmarks. The
resulting tarball provides the evidence needed to diagnose query failures, missing clinical
references, citation linking errors, and compliance logging gaps without requiring direct
OpenEvidence dashboard access.

## Prerequisites

- `curl`, `jq`, `tar` installed
- `OPENEVIDENCE_API_KEY` set (API key from OpenEvidence developer portal)
- Network access to `api.openevidence.com` (HTTPS 443)

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-openevidence-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "API Key: ${OPENEVIDENCE_API_KEY:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Node: $(node -v 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Python: $(python3 --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# API connectivity — health check
echo "=== API Health ===" > "$BUNDLE/api-health.txt"
curl -sf -o "$BUNDLE/api-health.txt" -w "HTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  "https://api.openevidence.com/v1/health" 2>&1 || echo "UNREACHABLE" > "$BUNDLE/api-health.txt"

# Clinical query test (benign test query)
echo "=== Query Test ===" > "$BUNDLE/query-test.json"
curl -sf -X POST "https://api.openevidence.com/v1/query" \
  -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the recommended first-line treatment for hypertension?","max_results":3}' \
  >> "$BUNDLE/query-test.json" 2>&1 || echo '{"error":"QUERY_FAILED"}' > "$BUNDLE/query-test.json"

# Evidence citation retrieval
echo "=== Citations ===" > "$BUNDLE/citations.json"
QUERY_ID=$(jq -r '.queryId // empty' "$BUNDLE/query-test.json" 2>/dev/null)
if [ -n "${QUERY_ID:-}" ]; then
  curl -sf -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
    "https://api.openevidence.com/v1/citations/${QUERY_ID}" \
    >> "$BUNDLE/citations.json" 2>&1 || echo '{"error":"CITATION_FAILED"}' > "$BUNDLE/citations.json"
else
  echo '{"error":"No query ID — skipping citation check"}' > "$BUNDLE/citations.json"
fi

# Model version metadata
echo "=== Model Info ===" > "$BUNDLE/model-info.json"
curl -sf -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  "https://api.openevidence.com/v1/models" \
  >> "$BUNDLE/model-info.json" 2>&1 || echo '{"error":"MODEL_INFO_FAILED"}' > "$BUNDLE/model-info.json"

# Recent logs
echo "=== Recent Logs ===" > "$BUNDLE/app-logs.txt"
tail -100 /var/log/openevidence-integration/*.log >> "$BUNDLE/app-logs.txt" 2>/dev/null || echo "No integration logs found" >> "$BUNDLE/app-logs.txt"

# Rate limit status
echo "=== Rate Limits ===" > "$BUNDLE/rate-limits.txt"
curl -sI -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  "https://api.openevidence.com/v1/health" 2>/dev/null | grep -i "x-rate\|retry-after\|x-ratelimit" >> "$BUNDLE/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE/rate-limits.txt"

# Package versions
echo "=== Dependencies ===" > "$BUNDLE/deps.txt"
pip list 2>/dev/null | grep -i openevidence >> "$BUNDLE/deps.txt" || echo "No OpenEvidence pip packages found" >> "$BUNDLE/deps.txt"
npm ls 2>/dev/null | grep -i openevidence >> "$BUNDLE/deps.txt" || echo "No OpenEvidence npm packages found" >> "$BUNDLE/deps.txt"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-openevidence-*.tar.gz
cat debug-openevidence-*/environment.txt        # Verify API key is set
cat debug-openevidence-*/api-health.txt         # Check HTTP status and latency
jq '.answer' debug-openevidence-*/query-test.json       # Review clinical response
jq '.citations | length' debug-openevidence-*/citations.json  # Count evidence sources
jq '.modelVersion' debug-openevidence-*/model-info.json  # Check active model
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| 401 Unauthorized | `environment.txt` shows key NOT SET | Generate new API key in OpenEvidence developer portal |
| Query returns generic response | `query-test.json` missing clinical specifics | Increase `max_results`; add clinical context (age, comorbidities) to query body |
| Citations array empty | `citations.json` has zero entries | Evidence retrieval may lag query by 2-5s; add `?wait=true` parameter to citation request |
| 503 Service Unavailable | `api-health.txt` shows 503 | Check OpenEvidence status page; clinical model reloads can cause 30-60s downtime windows |
| High latency (>10s) | `api-health.txt` shows time_total > 10s | Complex clinical queries take longer; use streaming endpoint for real-time responses |
| Rate limited on query endpoint | `rate-limits.txt` shows retry-after | Clinical query limit is 60 req/min; queue requests with exponential backoff |

## Automated Health Check

```typescript
async function checkOpenEvidenceHealth(): Promise<{
  status: string;
  latencyMs: number;
  apiReachable: boolean;
  queryWorking: boolean;
  modelVersion: string;
}> {
  const apiKey = process.env.OPENEVIDENCE_API_KEY;
  const headers = {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
  const start = Date.now();

  const healthRes = await fetch("https://api.openevidence.com/v1/health", {
    headers: { Authorization: `Bearer ${apiKey}` },
  });

  const queryRes = await fetch("https://api.openevidence.com/v1/query", {
    method: "POST",
    headers,
    body: JSON.stringify({
      query: "What is the recommended first-line treatment for hypertension?",
      max_results: 1,
    }),
  });

  let modelVersion = "unknown";
  try {
    const modelRes = await fetch("https://api.openevidence.com/v1/models", {
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    if (modelRes.ok) {
      const data = await modelRes.json();
      modelVersion = data.modelVersion ?? "unknown";
    }
  } catch { /* model endpoint optional */ }

  return {
    status: healthRes.ok && queryRes.ok ? "healthy" : "degraded",
    latencyMs: Date.now() - start,
    apiReachable: healthRes.ok,
    queryWorking: queryRes.ok,
    modelVersion,
  };
}
```

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)
- [OpenEvidence API Docs](https://docs.openevidence.com)
- [OpenEvidence Status](https://status.openevidence.com)

## Next Steps

See `openevidence-rate-limits`.
