---
name: clari-common-errors
description: |
  Diagnose and fix Clari API errors including auth failures, export issues, and data mismatches.
  Use when Clari API calls fail, exports return empty data,
  or forecast numbers do not match the UI.
  Trigger with phrases like "clari error", "clari not working",
  "clari api failure", "fix clari", "debug clari".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari Common Errors

## Overview

Diagnostic guide for the most common Clari API issues: authentication failures, empty exports, job timeouts, and data discrepancies.

## Error Reference

### 1. 401 Unauthorized
```
{"error": "Unauthorized", "message": "Invalid API key"}
```
**Fix**: Regenerate token at Clari > User Settings > API Token. Tokens may expire or be revoked by admins.

### 2. 403 Forbidden -- API Access Not Enabled
```
{"error": "Forbidden", "message": "API access not enabled for this user"}
```
**Fix**: Contact your Clari admin to enable API access. Requires enterprise plan.

### 3. 404 Forecast Not Found
```
{"error": "Not Found", "message": "Forecast 'wrong_name' not found"}
```
**Fix**: List available forecasts first:
```bash
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list | jq '.forecasts[].forecastName'
```

### 4. Export Returns Empty Entries
The API returns `{"entries": []}` with no error.

**Causes:**
- Time period has no submitted forecasts
- User lacks visibility into the forecast hierarchy
- Wrong forecast name (case-sensitive)

**Fix**: Verify in Clari UI that the forecast has submissions for the requested period.

### 5. Job Stuck in PENDING
Export job never reaches COMPLETED status.

**Causes:**
- Very large export (all reps, all periods)
- Clari backend queue congestion

**Fix**: Increase polling timeout. Break large exports into per-period batches.

### 6. Data Mismatch Between API and UI
Forecast numbers from API do not match what is shown in Clari UI.

**Causes:**
- API exports submitted calls, UI may show latest-edited values
- Currency conversion differences
- Time period boundary differences (calendar vs fiscal)

**Fix**: Use `includeHistorical: true` to get all submission versions. Match the exact time period label from the UI.

### 7. Copilot API OAuth Errors
```
{"error": "invalid_client"}
```
**Fix**: The Copilot API uses OAuth2, not API key auth. Register your app at https://api-doc.copilot.clari.com and use client credentials flow.

### 8. Rate Limit Exceeded
```
HTTP 429 Too Many Requests
```
**Fix**: Implement exponential backoff. See `clari-rate-limits` for patterns.

## Quick Diagnostic Commands

```bash
# Test API key
curl -s -o /dev/null -w "%{http_code}" \
  -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list

# List all forecasts
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/forecast/list | jq .

# Check running jobs
curl -s -H "apikey: ${CLARI_API_KEY}" \
  https://api.clari.com/v4/export/jobs | jq '.jobs[] | {jobId, status, createdAt}'
```

## Resources

- [Clari Developer Portal](https://developer.clari.com)
- [Clari Community](https://community.clari.com)

## Next Steps

For comprehensive diagnostics, see `clari-debug-bundle`.
