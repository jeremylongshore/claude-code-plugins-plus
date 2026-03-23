---
name: notion-incident-runbook
description: |
  Execute Notion incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Notion API outages, investigating errors,
  or running post-incident reviews for Notion integration failures.
  Trigger with phrases like "notion incident", "notion outage",
  "notion down", "notion on-call", "notion emergency", "notion broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Incident Runbook

## Overview

Rapid incident response procedures for Notion API failures. This runbook covers a structured triage flow (under 5 minutes), automated health checks against both status.notion.so and your own integration, a decision tree for classifying failures (Notion-side vs. integration-side), per-error-type mitigation with real `Client` code, cached fallback patterns, communication templates, and postmortem structure.

## Prerequisites

- Access to application monitoring dashboards and log aggregator
- `NOTION_TOKEN` environment variable set for diagnostic API calls
- `curl` and `jq` installed for quick CLI triage
- Python alternative: `notion-client` (`pip install notion-client`)
- Communication channels configured (Slack webhook, PagerDuty, etc.)

## Instructions

### Step 1: Quick Triage (Under 5 Minutes)

Run this diagnostic script to determine if the issue is Notion-side or integration-side:

```bash
#!/bin/bash
# notion-triage.sh — run at first alert
set -euo pipefail
echo "=== Notion Incident Triage ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Check Notion's public status page
echo -e "\n--- Notion Platform Status ---"
STATUS=$(curl -sf https://status.notion.so/api/v2/status.json \
  | jq -r '.status.description' 2>/dev/null || echo "UNREACHABLE")
echo "Notion Status: $STATUS"

INCIDENTS=$(curl -sf https://status.notion.so/api/v2/incidents/unresolved.json \
  | jq '.incidents | length' 2>/dev/null || echo "UNKNOWN")
echo "Active Incidents: $INCIDENTS"

if [ "$INCIDENTS" != "0" ] && [ "$INCIDENTS" != "UNKNOWN" ]; then
  echo "INCIDENT DETAILS:"
  curl -sf https://status.notion.so/api/v2/incidents/unresolved.json \
    | jq -r '.incidents[] | "  - \(.name) (\(.status)): \(.incident_updates[0].body)"'
fi

# 2. Test our integration authentication
echo -e "\n--- Integration Auth Check ---"
AUTH_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" \
  https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" 2>/dev/null || echo "000")
echo "Auth HTTP Status: $AUTH_HTTP"

if [ "$AUTH_HTTP" = "200" ]; then
  BOT_NAME=$(curl -sf https://api.notion.com/v1/users/me \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28" | jq -r '.name')
  echo "Bot Name: $BOT_NAME"
fi

# 3. Test database query (if test DB configured)
echo -e "\n--- API Responsiveness ---"
if [ -n "${NOTION_TEST_DATABASE_ID:-}" ]; then
  QUERY_RESULT=$(curl -sf -o /dev/null -w "%{http_code} %{time_total}s" \
    -X POST "https://api.notion.com/v1/databases/${NOTION_TEST_DATABASE_ID}/query" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28" \
    -H "Content-Type: application/json" \
    -d '{"page_size": 1}' 2>/dev/null || echo "000 0.000s")
  echo "Database Query: $QUERY_RESULT"
else
  echo "NOTION_TEST_DATABASE_ID not set — skipping query test"
fi

# 4. Classification
echo -e "\n--- Triage Result ---"
if [ "$STATUS" != "All Systems Operational" ] && [ "$STATUS" != "UNREACHABLE" ]; then
  echo "CLASSIFICATION: Notion-side issue. Enable fallback mode."
elif [ "$AUTH_HTTP" = "401" ]; then
  echo "CLASSIFICATION: Token expired or revoked. Rotate immediately."
elif [ "$AUTH_HTTP" = "429" ]; then
  echo "CLASSIFICATION: Rate limited. Reduce concurrency."
elif [ "$AUTH_HTTP" = "000" ]; then
  echo "CLASSIFICATION: Network/DNS issue. Check firewall and DNS."
else
  echo "CLASSIFICATION: Integration-side issue. Check application logs."
fi
```

**TypeScript — programmatic triage:**

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

async function triageNotionHealth(token: string): Promise<{
  classification: string;
  notionStatus: string;
  authStatus: string;
  latencyMs: number;
}> {
  // Check Notion status page
  let notionStatus = 'unknown';
  try {
    const res = await fetch('https://status.notion.so/api/v2/status.json');
    const data = await res.json();
    notionStatus = data.status.description;
  } catch { notionStatus = 'unreachable'; }

  // Test our authentication
  const client = new Client({ auth: token, timeoutMs: 10_000 });
  const start = Date.now();
  let authStatus = 'unknown';
  let classification = 'unknown';

  try {
    await client.users.me({});
    authStatus = 'authenticated';
    classification = 'integration-side';
  } catch (error) {
    if (isNotionClientError(error)) {
      authStatus = `${error.code} (HTTP ${error.status})`;
      switch (error.code) {
        case APIErrorCode.Unauthorized:
          classification = 'token-expired';
          break;
        case APIErrorCode.RateLimited:
          classification = 'rate-limited';
          break;
        case APIErrorCode.ServiceUnavailable:
          classification = 'notion-down';
          break;
        default:
          classification = 'api-error';
      }
    } else {
      authStatus = 'network-error';
      classification = 'network-issue';
    }
  }

  if (notionStatus !== 'All Systems Operational') {
    classification = 'notion-side';
  }

  return {
    classification,
    notionStatus,
    authStatus,
    latencyMs: Date.now() - start,
  };
}
```

### Step 2: Decision Tree and Mitigation

```
Is status.notion.so showing an incident?
|
+-- YES --> Notion-side outage
|   +-- Enable cached/fallback mode
|   +-- Notify users of degraded service
|   +-- Monitor status page for resolution
|   +-- DO NOT restart or rotate tokens
|
+-- NO --> Our integration issue
    |
    +-- Auth returning 401?
    |   +-- YES --> Token expired or revoked
    |   |   +-- Regenerate at notion.so/my-integrations
    |   |   +-- Update secret manager (see below)
    |   |   +-- Restart application
    |   +-- NO --> Continue
    |
    +-- Getting 429 rate limits?
    |   +-- YES --> Exceeding 3 req/s average
    |   |   +-- Check for runaway loops or webhook storms
    |   |   +-- Reduce concurrency to 1
    |   |   +-- Add exponential backoff
    |   +-- NO --> Continue
    |
    +-- Getting 404 on specific resources?
    |   +-- YES --> Pages unshared or deleted
    |   |   +-- Re-share pages with integration via Connections menu
    |   |   +-- Check if pages were moved to trash
    |   +-- NO --> Continue
    |
    +-- Getting 400 validation errors?
    |   +-- YES --> Database schema changed in Notion UI
    |   |   +-- Re-fetch schema (databases.retrieve)
    |   |   +-- Compare with expected properties
    |   |   +-- Update property mappings in code
    |   +-- NO --> Investigate application logs
```

**Token rotation:**

```bash
# AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id notion/production \
  --secret-string '{"token":"ntn_NEW_TOKEN_HERE"}'

# GCP Secret Manager
echo -n "ntn_NEW_TOKEN_HERE" | \
  gcloud secrets versions add notion-token-prod --data-file=-

# Restart to pick up new token
kubectl rollout restart deployment/my-app  # Kubernetes
# or: gcloud run services update my-service --no-traffic  # Cloud Run
```

**Cached fallback for Notion outages:**

```typescript
import { Client, isNotionClientError } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN! });
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

async function queryWithFallback(dbId: string, filter?: any) {
  const cacheKey = `query:${dbId}:${JSON.stringify(filter)}`;

  try {
    const result = await notion.databases.query({
      database_id: dbId,
      filter,
      page_size: 100,
    });

    // Update cache on success
    cache.set(cacheKey, { data: result, timestamp: Date.now() });
    return { data: result, source: 'live' as const };
  } catch (error) {
    // Fall back to cache on any API error
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      console.warn(`Notion unavailable, serving cached data (age: ${
        Math.round((Date.now() - cached.timestamp) / 1000)
      }s)`);
      return { data: cached.data, source: 'cache' as const };
    }

    // No cache available — re-throw
    throw error;
  }
}

// Schema change detection
async function detectSchemaChanges(dbId: string, expectedProps: string[]) {
  const db = await notion.databases.retrieve({ database_id: dbId });
  const actualProps = Object.keys(db.properties);

  const missing = expectedProps.filter(p => !actualProps.includes(p));
  const unexpected = actualProps.filter(p => !expectedProps.includes(p));

  if (missing.length > 0 || unexpected.length > 0) {
    console.error(JSON.stringify({
      event: 'schema_change_detected',
      database_id: dbId,
      missing_properties: missing,
      new_properties: unexpected,
    }));
  }

  return { missing, unexpected, current: actualProps };
}
```

### Step 3: Communication and Postmortem

**Internal Slack notification template:**

```
:rotating_light: P[1-4] INCIDENT: Notion Integration
Status: [INVESTIGATING | MITIGATING | RESOLVED]
Impact: [specific user-facing impact]
Root Cause: [Notion outage | Token expired | Rate limited | Schema change]
Action: [current remediation step]
ETA: [estimated resolution or "monitoring"]
Dashboard: [link to monitoring dashboard]
Thread: [link to incident channel thread]
```

**External status page update:**

```
Notion Integration Service Disruption

We are experiencing [brief description of impact]. [Specific feature]
may be unavailable or show stale data.

Workaround: [if available, e.g., "Cached data is being served"]
Next update: [time, e.g., "in 30 minutes or sooner if resolved"]

[ISO 8601 timestamp]
```

**Postmortem template:**

```markdown
## Incident: Notion [Error Type] — [Date]
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Detection:** [Alert name] / [User report]

### Summary
[1-2 sentence description of what happened and the user impact]

### Timeline (all times UTC)
- HH:MM — First alert fired ([alert name])
- HH:MM — On-call acknowledged, began triage
- HH:MM — Root cause identified: [description]
- HH:MM — Mitigation applied: [action taken]
- HH:MM — Service fully restored

### Root Cause
[Technical explanation — e.g., "Integration token was rotated in Notion
dashboard by a team member without updating the secret manager, causing
all API calls to return 401 Unauthorized."]

### Impact
- Users affected: N
- Duration of degraded service: X minutes
- Data loss: [none | description]

### Action Items
| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P1 | [Preventive measure] | @name | YYYY-MM-DD |
| P2 | [Detection improvement] | @name | YYYY-MM-DD |
| P3 | [Process improvement] | @name | YYYY-MM-DD |
```

## Output

- Automated triage script classifying incidents in under 5 minutes
- Decision tree mapping HTTP status codes to root causes
- Per-error-type mitigation procedures with real code
- Cached fallback mode for Notion outages
- Schema change detection for 400 validation errors
- Communication templates for internal and external stakeholders
- Postmortem template with timeline and action items

## Error Handling

| Scenario | Triage Signal | Immediate Action |
|----------|--------------|------------------|
| Notion platform outage | status.notion.so incident | Enable fallback mode, notify users |
| Token expired/revoked | All requests return 401 | Rotate token in secret manager, restart |
| Rate limited | 429 errors spiking | Reduce concurrency to 1, check for loops |
| Schema changed | 400 on specific operations | Run `databases.retrieve`, update mappings |
| Network/DNS issue | Timeouts, no HTTP response | Check firewall, DNS resolution, proxy config |
| Pages unshared | 404 on previously working pages | Re-share via Connections menu in Notion |

## Examples

### One-Line Health Check

```bash
curl -sf https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  | jq '{name: .name, type: .type}' \
  || echo "UNHEALTHY: Notion API unreachable or auth failed"
```

### Python Quick Triage

```python
from notion_client import Client, APIResponseError
import os

def quick_triage():
    try:
        client = Client(auth=os.environ["NOTION_TOKEN"], timeout_ms=10_000)
        me = client.users.me()
        print(f"OK: Connected as {me['name']}")
    except APIResponseError as e:
        print(f"ERROR: {e.code} (HTTP {e.status}): {e.message}")
    except Exception as e:
        print(f"NETWORK ERROR: {e}")

quick_triage()
```

## Resources

- [Notion Status Page](https://status.notion.so) — real-time platform status
- [Notion API Error Codes](https://developers.notion.com/reference/errors) — full error reference
- [Notion Request Limits](https://developers.notion.com/reference/request-limits) — 3 req/s average
- [Statuspage API](https://www.atlassianstatuspage.io/api) — programmatic status checks

## Next Steps

For data handling and privacy compliance, see `notion-data-handling`.
