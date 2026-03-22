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
Rapid incident response procedures for Notion API failures: triage, mitigation, communication, and postmortem.

## Prerequisites
- Access to application monitoring and logs
- Notion token for diagnostic API calls
- Communication channels (Slack, PagerDuty)

## Instructions

### Step 1: Quick Triage (< 5 minutes)
```bash
#!/bin/bash
echo "=== Notion Incident Triage ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Is Notion itself down?
echo -e "\n--- Notion Platform Status ---"
STATUS=$(curl -s https://status.notion.com/api/v2/status.json | jq -r '.status.description')
echo "Notion Status: $STATUS"

INCIDENTS=$(curl -s https://status.notion.com/api/v2/incidents/unresolved.json | jq '.incidents | length')
echo "Active Incidents: $INCIDENTS"

# 2. Can our integration authenticate?
echo -e "\n--- Integration Auth ---"
AUTH_RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28")
echo "Auth HTTP: $AUTH_RESULT"

# 3. Can we query a database?
echo -e "\n--- API Responsiveness ---"
if [ -n "$NOTION_TEST_DATABASE_ID" ]; then
  API_RESULT=$(curl -s -o /dev/null -w "%{http_code} %{time_total}s" \
    -X POST "https://api.notion.com/v1/databases/${NOTION_TEST_DATABASE_ID}/query" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28" \
    -H "Content-Type: application/json" \
    -d '{"page_size": 1}')
  echo "Query: $API_RESULT"
fi
```

### Step 2: Decision Tree
```
Is Notion status page showing an incident?
├─ YES → Notion-side issue
│   ├─ Enable fallback/cached mode
│   ├─ Notify users of degraded service
│   └─ Monitor status.notion.com for resolution
│
└─ NO → Our integration issue
    ├─ Auth returning 401?
    │   ├─ YES → Token expired or revoked
    │   │   └─ Regenerate at notion.so/my-integrations
    │   └─ NO → Continue
    │
    ├─ Getting 429 rate limits?
    │   ├─ YES → Too many requests
    │   │   └─ Check for runaway loops, reduce concurrency
    │   └─ NO → Continue
    │
    ├─ Getting 404 on specific resources?
    │   ├─ YES → Pages unshared or deleted
    │   │   └─ Re-share pages with integration
    │   └─ NO → Continue
    │
    └─ Getting 400 validation errors?
        ├─ YES → Schema changed in Notion
        │   └─ Check if properties were renamed/removed
        └─ NO → Investigate application code
```

### Step 3: Immediate Mitigation by Error Type

**Token Expired (401):**
```bash
# Regenerate token at notion.so/my-integrations
# Update in secret manager
aws secretsmanager update-secret --secret-id notion-token --secret-string "ntn_new_xxx"
# Or: gcloud secrets versions add notion-token --data-file=-

# Restart application to pick up new token
# Platform-specific restart command
```

**Rate Limited (429):**
```typescript
// Temporary: reduce request concurrency
// In application code or environment variable:
process.env.NOTION_MAX_CONCURRENCY = '1'; // Reduce from default

// Check for request loops
// Look for patterns like:
// - Webhook handler that triggers another webhook
// - Polling that creates pages (which triggers more polling)
// - Retry logic without backoff
```

**Notion Down (502/503):**
```typescript
// Enable cached/fallback mode
async function getDatabaseWithFallback(dbId: string) {
  try {
    const result = await notion.databases.query({ database_id: dbId });
    await updateCache(dbId, result);
    return { data: result, source: 'live' };
  } catch (error) {
    const cached = await getCache(dbId);
    if (cached) {
      return { data: cached, source: 'cache' };
    }
    throw error;
  }
}
```

**Schema Changed (400 validation_error):**
```typescript
// Re-fetch database schema to see what changed
const db = await notion.databases.retrieve({ database_id: dbId });
console.log('Current schema:');
for (const [name, prop] of Object.entries(db.properties)) {
  console.log(`  ${name}: ${prop.type}`);
}
// Compare with expected schema and update code
```

### Step 4: Communication Templates

**Internal (Slack):**
```
P[1-4] INCIDENT: Notion Integration
Status: [INVESTIGATING | MITIGATING | RESOLVED]
Impact: [specific user impact]
Root Cause: [Notion outage | Token expired | Rate limited | Schema change]
Action: [what's being done]
ETA: [estimated resolution time]
```

**External (Status Page):**
```
Notion Integration Disruption

We're experiencing [brief description]. [Specific feature] may be
unavailable or show stale data.

Workaround: [if any]
Next update: [time]

[timestamp]
```

### Step 5: Postmortem Template
```markdown
## Incident: Notion [Error Type]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]

### Summary
[1-2 sentence description]

### Timeline
- HH:MM UTC — First alert
- HH:MM UTC — Investigation began
- HH:MM UTC — Root cause identified
- HH:MM UTC — Mitigation applied
- HH:MM UTC — Fully resolved

### Root Cause
[Technical explanation — e.g., "Token was regenerated in Notion dashboard
without updating the secret manager"]

### Impact
- Users affected: N
- Duration of degraded service: X minutes

### Action Items
- [ ] [Preventive measure] — Owner — Due date
- [ ] [Detection improvement] — Owner — Due date
```

## Output
- Issue triaged within 5 minutes
- Root cause category identified
- Mitigation applied (fallback, token rotation, rate reduction)
- Stakeholders notified
- Evidence collected for postmortem

## Error Handling
| Scenario | Triage Signal | Action |
|----------|--------------|--------|
| Notion outage | status.notion.com incident | Enable fallback mode |
| Token expired | All requests return 401 | Rotate token |
| Rate limited | 429 errors spiking | Reduce concurrency |
| Schema change | 400 errors on specific operations | Re-fetch schema |
| Network issue | Timeouts, no response | Check DNS, firewall |

## Examples

### One-Line Health Check
```bash
curl -sf https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq .name || echo "UNHEALTHY"
```

## Resources
- [Notion Status Page](https://status.notion.com)
- [Notion API Error Codes](https://developers.notion.com/reference/request-limits)
- [Notion Developer Community](https://developers.notion.com)

## Next Steps
For data handling compliance, see `notion-data-handling`.
