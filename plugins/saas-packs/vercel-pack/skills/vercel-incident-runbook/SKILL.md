---
name: vercel-incident-runbook
description: |
  Vercel incident response procedures with triage, instant rollback, and postmortem.
  Use when responding to Vercel-related outages, investigating production errors,
  or running post-incident reviews for deployment failures.
  Trigger with phrases like "vercel incident", "vercel outage",
  "vercel down", "vercel on-call", "vercel emergency", "vercel broken".
allowed-tools: Read, Grep, Bash(vercel:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, incident-response, runbook]

---
# Vercel Incident Runbook

## Overview
Step-by-step incident response for Vercel deployment failures, function errors, and platform outages. Covers rapid triage, instant rollback, communication templates, and postmortem procedures.

## Prerequisites
- Access to Vercel dashboard and CLI
- Access to Vercel status page (vercel-status.com)
- Communication channels (Slack, PagerDuty) configured
- Log drain or runtime log access

## Instructions

### Step 1: Rapid Triage (First 5 Minutes)
```bash
# 1. Check if it's a Vercel platform issue
curl -s "https://www.vercel-status.com/api/v2/summary.json" \
  | jq '.status.description, [.components[] | select(.status != "operational") | {name, status}]'

# 2. Check current production deployment status
vercel ls --prod
vercel inspect $(vercel ls --prod --json | jq -r '.[0].url')

# 3. Check recent deployments — did a deploy just happen?
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v6/deployments?target=production&limit=5&projectId=prj_xxx" \
  | jq '.deployments[] | {uid, state, createdAt: (.createdAt/1000 | todate), url}'

# 4. Check function logs for errors
vercel logs $(vercel ls --prod --json | jq -r '.[0].url') --level=error --limit=20
```

### Step 2: Decision Tree
```
Is vercel-status.com showing an incident?
├── YES → Vercel platform issue
│   ├── Subscribe to updates on status page
│   ├── Post internal status: "Vercel platform incident — monitoring"
│   └── No action needed from us — wait for Vercel resolution
│
└── NO → Issue is in our deployment
    ├── Did a deployment happen in the last 30 minutes?
    │   ├── YES → Likely deployment regression
    │   │   └── ROLLBACK immediately (Step 3)
    │   └── NO → Application-level issue
    │       ├── Check function logs for new errors
    │       ├── Check external dependency status (DB, APIs)
    │       └── Investigate and hotfix (Step 4)
    │
    └── Is the issue region-specific?
        ├── YES → Check function regions, possible edge issue
        └── NO → Global issue, check code and env vars
```

### Step 3: Instant Rollback (< 30 Seconds)
```bash
# Option A: Rollback to previous production deployment (fastest)
vercel rollback
# This instantly swaps production traffic — no rebuild needed

# Option B: Rollback to a specific known-good deployment
vercel rollback dpl_xxxxxxxxxxxx

# Option C: Via API (for automation/PagerDuty integration)
curl -X POST "https://api.vercel.com/v9/projects/my-app/promote" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"deploymentId": "dpl_known_good_id"}'

# Verify rollback succeeded
vercel ls --prod
curl -s https://yourdomain.com/api/health | jq .
```

### Step 4: Investigate Root Cause
```bash
# Collect evidence while it's fresh
mkdir incident-$(date +%Y%m%d)
cd incident-$(date +%Y%m%d)

# Function logs around the incident time
vercel logs https://yourdomain.com --limit=200 > function-logs.txt

# Deployment diff — what changed?
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/dpl_broken" \
  | jq '.meta' > broken-deployment-meta.json

# Compare env vars between working and broken deployments
vercel env ls > env-vars.txt

# Check git diff between last good and broken commit
git log --oneline -10
git diff dpl_good_commit..dpl_broken_commit -- api/ src/
```

### Step 5: Enable Maintenance Page (If Needed)
```json
// vercel.json — temporary maintenance mode via rewrite
{
  "rewrites": [
    {
      "source": "/((?!_next|api/health).*)",
      "destination": "/maintenance.html"
    }
  ]
}
```

```html
<!-- public/maintenance.html -->
<!DOCTYPE html>
<html>
<head><title>Maintenance</title></head>
<body>
  <h1>We'll be right back</h1>
  <p>We're performing scheduled maintenance. Please check back shortly.</p>
</body>
</html>
```

### Step 6: Communication Templates

**Internal — Slack (Incident Start)**
```
:rotating_light: INCIDENT: [Project Name] production issue detected
Status: Investigating
Impact: [Description of user impact]
Start time: [UTC timestamp]
On-call: @[engineer]
Thread: replies here
```

**Internal — Slack (Mitigation)**
```
:white_check_mark: MITIGATED: [Project Name]
Action: Rolled back to deployment dpl_xxx
Impact duration: [X minutes]
Root cause: [Brief description]
Postmortem: [link] scheduled for [date]
```

**External — Status Page**
```
Title: Degraded performance on [service]
Body: We are investigating reports of [issue]. Some users may experience
[impact]. Our team is actively working on a resolution.
Update: The issue has been resolved. [Brief root cause].
```

### Step 7: Postmortem Template
```markdown
# Incident Postmortem: [Title]

## Summary
- Duration: [start] to [end] ([X minutes])
- Impact: [users/requests affected]
- Severity: [P1/P2/P3]

## Timeline (UTC)
- HH:MM — [event]
- HH:MM — Alert fired
- HH:MM — On-call acknowledged
- HH:MM — Root cause identified
- HH:MM — Rollback executed
- HH:MM — Service restored

## Root Cause
[What broke and why]

## Resolution
[What was done to fix it]

## Action Items
- [ ] [Preventive action] — Owner: @xxx — Due: [date]
- [ ] [Detection improvement] — Owner: @xxx — Due: [date]
- [ ] [Process improvement] — Owner: @xxx — Due: [date]
```

## Incident Severity Levels

| Severity | Definition | Response Time | Rollback? |
|----------|-----------|---------------|-----------|
| P1 | Production down, all users affected | < 5 min | Immediate |
| P2 | Degraded, some users affected | < 15 min | If not fixable in 30 min |
| P3 | Minor issue, workaround exists | < 1 hour | No |
| P4 | Cosmetic or non-urgent | Next business day | No |

## Output
- Incident categorized and triaged within 5 minutes
- Instant rollback executed if deployment regression detected
- Communication sent to internal and external stakeholders
- Postmortem scheduled with action items

## Error Handling
| Scenario | Action |
|----------|--------|
| Vercel status page shows incident | Monitor, communicate, no deployment changes |
| `vercel rollback` fails | Use API promotion: POST to `/v9/projects/.../promote` |
| Rollback deployment also broken | Deploy from a known-good git tag |
| Cannot access Vercel dashboard | Use CLI with saved VERCEL_TOKEN |
| Log retention expired | Check external log drain provider |

## Resources
- [Vercel Status Page](https://www.vercel-status.com)
- [Instant Rollback](https://vercel.com/docs/instant-rollback)
- [Vercel Support](https://vercel.com/support)
- [Vercel Logs CLI](https://vercel.com/docs/cli/logs)

## Next Steps
For data handling and compliance, see `vercel-data-handling`.
