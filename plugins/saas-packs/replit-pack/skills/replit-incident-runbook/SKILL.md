---
name: replit-incident-runbook
description: |
  Execute Replit incident response: triage deployment failures, database issues, and platform outages.
  Use when responding to Replit-related outages, investigating deployment crashes,
  or running post-incident reviews for Replit app failures.
  Trigger with phrases like "replit incident", "replit outage",
  "replit down", "replit emergency", "replit broken", "replit crash".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, incident-response, debugging]

---
# Replit Incident Runbook

## Overview
Rapid incident response for Replit deployment failures, database issues, and platform outages. Covers triage, diagnosis, remediation, rollback, and communication.

## Prerequisites
- Access to Replit Workspace and Deployment settings
- Deployment URL for health checks
- Communication channel (Slack, email)
- Rollback awareness (Deployment History)

## Severity Levels
| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | App returns 5xx, DB down |
| P2 | Degraded service | < 1 hour | Slow responses, intermittent errors |
| P3 | Minor impact | < 4 hours | Non-critical feature broken |
| P4 | No user impact | Next business day | Monitoring gap |

## Quick Triage (First 5 Minutes)

```bash
set -euo pipefail
DEPLOY_URL="https://your-app.replit.app"

echo "=== TRIAGE ==="

# 1. Check Replit platform status
echo -n "Replit Status: "
curl -s https://status.replit.com/api/v2/summary.json | \
  python3 -c "import sys,json;print(json.load(sys.stdin)['status']['description'])" 2>/dev/null || \
  echo "Check https://status.replit.com"

# 2. Check your deployment health
echo -n "App Health: "
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" "$DEPLOY_URL/health" 2>/dev/null || echo "UNREACHABLE"
echo ""

# 3. Get health details
echo "Health Response:"
curl -s "$DEPLOY_URL/health" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "No response"

# 4. Check if it's a cold start issue (Autoscale)
echo -n "Second request: "
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)\n" "$DEPLOY_URL/health"
```

## Decision Tree

```
App not responding?
├─ YES: Is status.replit.com reporting an incident?
│   ├─ YES → Platform issue. Wait for Replit. Communicate to users.
│   └─ NO → Your deployment issue. Continue below.
│
│   Can you access the Replit Workspace?
│   ├─ YES → Check deployment logs:
│   │   ├─ Build error → Fix code, redeploy
│   │   ├─ Runtime crash → Check logs, fix, redeploy
│   │   └─ Secret missing → Add to Secrets tab, redeploy
│   └─ NO → Network/browser issue. Try incognito window.
│
└─ App responds but with errors?
    ├─ 5xx errors → Check logs for crash/exception
    ├─ Slow responses → Check database, cold start, memory
    └─ Auth not working → Verify deployment domain, not dev URL
```

## Remediation by Error Type

### Deployment Crash (5xx / App Unreachable)
```markdown
1. Open Replit Workspace
2. Go to Deployment Settings > Logs
3. Look for the crash reason:
   - "Error: Cannot find module..." → Missing dependency
   - "FATAL: Missing secrets..." → Add to Secrets tab
   - "EADDRINUSE" → Port conflict in .replit config
   - "JavaScript heap out of memory" → Increase VM size or fix memory leak

4. Fix the issue in code
5. Click "Deploy" to redeploy
6. If fix is unclear, ROLLBACK:
   - Deployment Settings > History
   - Click "Rollback" on last known-good version
```

### Database Connection Failure
```markdown
1. Check database status in Database pane
2. Verify DATABASE_URL is set in Secrets
3. Test connection:
```
```bash
# From Replit Shell
node -e "
const {Pool} = require('pg');
const pool = new Pool({connectionString: process.env.DATABASE_URL, ssl:{rejectUnauthorized:false}});
pool.query('SELECT NOW()').then(r => console.log('OK:', r.rows[0])).catch(e => console.error('FAIL:', e.message)).finally(() => pool.end());
"
```
```markdown
4. If connection fails:
   - Check if PostgreSQL is provisioned (Database pane)
   - Try creating a new database
   - Check for connection pool exhaustion (max connections)
```

### Cold Start Too Slow (Autoscale)
```markdown
If cold starts exceed acceptable latency:
1. Check deployment type: Autoscale scales to zero
2. Options:
   a. Switch to Reserved VM (always-on, no cold starts)
   b. Set up external keep-alive (ping /health every 4 min)
   c. Optimize startup: lazy imports, defer DB connection
3. To switch:
   - Update .replit: deploymentTarget = "cloudrun"
   - Redeploy
```

### Secrets Missing After Deploy
```markdown
1. Open Secrets tab (lock icon in sidebar)
2. Verify all required secrets are present
3. Check Deployment Settings > Environment Variables
4. Secrets should auto-sync (2025+), but if not:
   - Remove and re-add the secret
   - Redeploy
5. For Account-level secrets:
   - Account Settings > Secrets
   - These apply to ALL Repls
```

## Rollback Procedure
```markdown
Replit supports one-click rollback to any previous deployment:

1. Deployment Settings > History
2. Find the last successful deployment
3. Click "Rollback to this version"
4. Verify health endpoint
5. Investigate root cause before redeploying fix

Rollback restores:
- Code at that deployment's commit
- Deployment configuration at that time
- Does NOT rollback database changes
```

## Communication Templates

### Internal (Slack)
```
P[1-4] INCIDENT: [App Name] on Replit
Status: INVESTIGATING / IDENTIFIED / MONITORING / RESOLVED
Impact: [What users are experiencing]
Cause: [If known]
Action: [What we're doing]
ETA: [When we expect resolution]
Next update: [Time]
```

### External (Status Page)
```
[App Name] Service Disruption

We are experiencing issues with [specific feature/service].
[Describe user impact].

We have identified the cause and are working on a fix.
Estimated resolution: [time].

Last updated: [timestamp]
```

## Post-Incident

### Evidence Collection
```bash
set -euo pipefail
# Capture deployment logs
# Go to Deployment Settings > Logs > Copy relevant entries

# Capture timeline
echo "Timeline of events:" > incident-report.md
echo "- [time] Issue detected" >> incident-report.md
echo "- [time] Investigation started" >> incident-report.md
echo "- [time] Root cause identified" >> incident-report.md
echo "- [time] Fix deployed / rollback executed" >> incident-report.md
echo "- [time] Service restored" >> incident-report.md
```

### Postmortem Template
```markdown
## Incident: [Title]
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]

### Summary
[1-2 sentence description of what happened]

### Root Cause
[Technical explanation]

### Timeline
- HH:MM — First alert
- HH:MM — Investigation started
- HH:MM — Root cause found
- HH:MM — Fix deployed / rollback
- HH:MM — Service restored

### Impact
- Users affected: [N]
- Downtime: [duration]

### Action Items
- [ ] [Prevention measure] — Owner — Due date
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't access Workspace | Replit outage | Use status.replit.com, wait |
| Rollback not available | No previous deployments | Fix forward, deploy fix |
| Logs too short | Container restarted | Set up external log aggregator |
| DB rollback needed | Bad migration | Restore from Replit DB snapshot |

## Resources
- [Replit Status](https://status.replit.com)
- [Deployment Rollbacks](https://blog.replit.com/introducing-deployment-rollbacks)
- [Monitoring Deployments](https://docs.replit.com/cloud-services/deployments/monitoring-a-deployment)
- [Replit Support](https://replit.com/support)

## Next Steps
For data handling patterns, see `replit-data-handling`.
