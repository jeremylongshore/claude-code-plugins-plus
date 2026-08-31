---
name: clari-common-errors
description: 'Diagnose and fix Clari API errors including auth failures, export issues,
  and data mismatches.

  Use when Clari API calls fail, exports return empty data,

  or forecast numbers do not match the UI.

  Trigger with phrases like "clari error", "clari not working",

  "clari api failure", "fix clari", "debug clari".

  '
allowed-tools: Read, Bash(curl:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- revenue-intelligence
- forecasting
- clari
compatibility: Designed for Claude Code
---
# Clari Common Errors

## Overview

Diagnostic guide for the most common Clari API issues: authentication failures, empty exports, job timeouts, and data discrepancies.

## Prerequisites

- Authorized, scoped access to the affected Clari environment
- Redacted job IDs, timestamps, and export metadata for diagnosis
- A named owner for credentials, forecast data, and production change approval
- Access to the certified prior dataset for safe comparison and recovery

## Instructions

Confirm the environment and affected period, collect the smallest redacted
evidence needed to classify the issue, then follow the matching reference
entry. Change one variable at a time and do not retry authentication, rate,
or data-integrity failures indefinitely. Escalate ambiguous provider behavior
with job IDs and timestamps rather than guessing at a production fix.

## Error Handling

| Failure class | Safe first response |
|---|---|
| Authentication or authorization | Stop retries and route to the credential/admin owner. |
| Empty, partial, or mismatched export | Mark the dataset uncertified and retain the prior certified output. |
| Timeout or rate limit | Preserve job state and resume through the bounded scheduler policy. |
| Suspected data exposure | Restrict access, notify governance, and use the incident process. |

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

## Output

Create a redacted incident record with environment, period, symptom, source
job/correlation ID, evidence, containment action, current data-certification
state, and escalation owner. Keep tokens, individual forecast values, and
download URLs out of diagnostic tickets and chat.

## Examples

When an export returns zero records, confirm the source period and job status,
mark the downstream refresh failed, and retain yesterday’s certified dataset.
When a request returns 401, stop the scheduler, verify the secret reference
with its owner, and rotate through the approved process instead of testing keys
in terminals or tickets.

## Resources

- [Clari Developer Portal](https://developer.clari.com)
- [Clari Community](https://community.clari.com)

## Next Steps

For comprehensive diagnostics, see `clari-debug-bundle`.
