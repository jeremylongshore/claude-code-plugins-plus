---
name: sentry-incident-runbook
description: |
  Incident response procedures using Sentry.
  Use when investigating production issues, triaging errors,
  or creating incident response workflows.
  Trigger with phrases like "sentry incident response", "sentry triage",
  "investigate sentry error", "sentry runbook".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, workflow, incident-response, triage]

---
# Sentry Incident Runbook

## Prerequisites
- Sentry account with access to project issues
- Alert rules configured for critical errors
- Team notification channels set up (Slack, PagerDuty)
- Access to Sentry API with auth token

## Instructions

### 1. Severity Classification

| Severity | Criteria | Response Time | Escalation |
|----------|----------|--------------|------------|
| **P0 — Critical** | Crash-free rate < 95%, payment failures, data loss | 15 min | PagerDuty on-call |
| **P1 — Major** | New error affecting > 100 users/hr, core feature broken | 1 hour | Slack #alerts-critical |
| **P2 — Minor** | New error affecting < 100 users/hr, workaround exists | Same day | Slack #alerts-production |
| **P3 — Low** | Edge case, cosmetic, staging-only | Next sprint | Backlog |

### 2. Initial Triage Checklist

When an alert fires:

```
[ ] 1. Open Sentry issue link from alert
[ ] 2. Check error frequency graph — is it spiking or steady?
[ ] 3. Check "First Seen" and "Last Seen" — is this new or recurring?
[ ] 4. Check affected users count
[ ] 5. Check environment — production, staging, or dev?
[ ] 6. Check release — which deployment introduced this?
[ ] 7. Read stack trace — identify the failing line
[ ] 8. Check breadcrumbs — what happened before the error?
[ ] 9. Check "Suspect Commits" — which commit likely caused it?
[ ] 10. Classify severity and communicate status
```

### 3. Sentry API for Incident Investigation

```bash
# Get issue details
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/issues/$ISSUE_ID/" \
  | python3 -c "
import json, sys
issue = json.load(sys.stdin)
print(f\"Title: {issue['title']}\")
print(f\"First Seen: {issue['firstSeen']}\")
print(f\"Last Seen: {issue['lastSeen']}\")
print(f\"Events: {issue['count']}\")
print(f\"Users: {issue['userCount']}\")
print(f\"Level: {issue['level']}\")
print(f\"Status: {issue['status']}\")
"

# Get latest events for the issue
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/issues/$ISSUE_ID/events/?per_page=5" \
  | python3 -c "
import json, sys
events = json.load(sys.stdin)
for e in events:
    print(f\"Event: {e['eventID']} | {e.get('dateCreated', 'N/A')} | Release: {e.get('release', {}).get('version', 'N/A')}\")
"
```

### 4. Error Pattern Identification

Common patterns and their likely causes:

**Deployment-related (error starts at deploy time):**
```
Diagnostic: Check "First Seen" time vs. latest deploy time
Fix: Rollback to previous release
  sentry-cli releases deploys "$PREVIOUS_VERSION" new --env production
```

**Third-party failure (external service errors):**
```
Diagnostic: Check error message for external hostnames
Check: Breadcrumbs showing failed HTTP calls
Fix: Enable circuit breaker, add retry logic, alert on dependency health
```

**Data corruption (validation/parsing errors):**
```
Diagnostic: Check event context for malformed data samples
Fix: Add input validation, fix data pipeline, backfill corrupted records
```

**Resource exhaustion (OOM, connection pool, timeouts):**
```
Diagnostic: Check error rate correlation with traffic
Fix: Scale resources, add connection pooling, implement rate limiting
```

### 5. Incident Communication Templates

**Initial Alert (within 15 min of P0):**
```
:rotating_light: INCIDENT — [Service Name]
Status: Investigating
Impact: [What users are experiencing]
Started: [Timestamp]
Sentry: [Link to issue]
Lead: @[on-call engineer]
Next update: 30 minutes
```

**Status Update (every 30 min for P0):**
```
UPDATE — [Service Name] Incident
Status: [Investigating | Identified | Monitoring | Resolved]
Root cause: [Brief description or "still investigating"]
Actions taken: [What's been done]
Next steps: [What's planned]
ETA: [When we expect resolution]
```

**Resolution:**
```
:white_check_mark: RESOLVED — [Service Name]
Duration: [X hours Y minutes]
Root cause: [What caused it]
Fix: [What was done]
Postmortem: [Link — due within 48 hours]
```

### 6. Resolving Issues in Sentry

```bash
# Mark issue as resolved
curl -X PUT \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved"}' \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/issues/$ISSUE_ID/"

# Resolve in next release (auto-reopens if it regresses)
curl -X PUT \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved", "statusDetails": {"inNextRelease": true}}' \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/issues/$ISSUE_ID/"

# Ignore issue (snooze — won't alert again)
curl -X PUT \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "ignored", "statusDetails": {"ignoreCount": 100}}' \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/issues/$ISSUE_ID/"
```

### 7. Postmortem Checklist

After resolution, complete within 48 hours:

```
[ ] Timeline of events (when detected, when mitigated, when resolved)
[ ] Root cause analysis (5 Whys)
[ ] Impact assessment (users affected, duration, revenue impact)
[ ] What went well (detection, response, communication)
[ ] What could improve (monitoring gaps, process issues)
[ ] Action items with owners and deadlines
[ ] Sentry configuration changes (new alerts, better grouping)
[ ] Prevention measures (tests, validation, monitoring)
```

## Output
- Severity classification framework (P0-P3)
- Triage checklist for rapid incident assessment
- API commands for investigating issues programmatically
- Communication templates for stakeholder updates
- Issue resolution via API (resolve, ignore, snooze)
- Postmortem checklist for continuous improvement

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Alert fatigue | Too many P2/P3 alerts | Tune alert thresholds, use "New issue" not "Every event" |
| Can't find root cause | Missing context in events | Add breadcrumbs, tags, and user context to SDK config |
| Issue keeps regressing | Resolved in current release but root cause not fixed | Use "Resolve in next release" to detect regressions |
| Suspect commits wrong | Commit association not configured | Set up `sentry-cli releases set-commits --auto` |

## Resources
- [Issue Details](https://docs.sentry.io/product/issues/issue-details/)
- [Alerts](https://docs.sentry.io/product/alerts/)
- [Issues API](https://docs.sentry.io/api/events/)
- [Ownership Rules](https://docs.sentry.io/product/issues/ownership-rules/)
