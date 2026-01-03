---
name: sentry-incident-runbook
description: |
  Incident response procedures using Sentry.
  Use when investigating production issues, triaging errors,
  or creating incident response workflows.
  Trigger with phrases like "sentry incident response", "sentry triage",
  "investigate sentry error", "sentry runbook".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Incident Runbook

## Overview
Standard procedures for investigating and resolving incidents using Sentry.

## Incident Severity Classification

### P0 - Critical
- **Definition:** Complete service outage, data loss risk
- **Sentry Indicators:**
  - Error rate > 50%
  - Fatal errors affecting all users
  - Database connection failures
- **Response Time:** Immediate (< 5 minutes)

### P1 - High
- **Definition:** Major feature broken, significant user impact
- **Sentry Indicators:**
  - Error rate 10-50%
  - Authentication failures
  - Payment processing errors
- **Response Time:** < 30 minutes

### P2 - Medium
- **Definition:** Feature degraded, workaround exists
- **Sentry Indicators:**
  - Error rate 1-10%
  - Non-critical API failures
  - Performance degradation
- **Response Time:** < 4 hours

### P3 - Low
- **Definition:** Minor issue, minimal user impact
- **Sentry Indicators:**
  - Error rate < 1%
  - Edge case errors
  - Non-blocking failures
- **Response Time:** Next business day

## Initial Triage Checklist

### Step 1: Assess Scope (2 minutes)
```
□ Check error rate trend in Sentry
□ Identify affected environments (prod/staging)
□ Count unique users affected
□ Check if new deployment coincides with errors
```

### Step 2: Gather Context (5 minutes)
```
□ Read error message and stack trace
□ Check breadcrumbs for user journey
□ Review tags (browser, OS, region)
□ Check for similar past issues
```

### Step 3: Identify Root Cause (10 minutes)
```
□ Check release/commit association
□ Review recent deployments
□ Check external service status
□ Analyze request/response data
```

## Sentry Investigation Commands

### Quick Issue Summary
```bash
# Get recent issues via API
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$ORG/$PROJECT/issues/?query=is:unresolved&limit=10"
```

### Get Issue Details
```bash
# Get specific issue
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/issues/$ISSUE_ID/"

# Get issue events
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/issues/$ISSUE_ID/events/"
```

### Check Release Health
```bash
# Get release stats
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$ORG/releases/$VERSION/"
```

## Common Issue Patterns

### Pattern 1: Deployment-Related Spike
**Symptoms:**
- Errors started immediately after deployment
- New error types not seen before
- Affected release matches latest deploy

**Resolution:**
1. Check commit associated with release
2. Rollback if critical
3. Hotfix if minor

### Pattern 2: Third-Party Service Failure
**Symptoms:**
- Network/timeout errors
- Errors reference external API
- Multiple users, single failure point

**Resolution:**
1. Check third-party status page
2. Enable fallback/cache if available
3. Add circuit breaker
4. Contact vendor if needed

### Pattern 3: Data/State Corruption
**Symptoms:**
- Unexpected null values
- Type errors
- Specific to certain users/records

**Resolution:**
1. Identify affected records
2. Check data migration history
3. Fix corrupted data
4. Add validation

### Pattern 4: Resource Exhaustion
**Symptoms:**
- Memory/timeout errors
- Gradual degradation
- Affects all users eventually

**Resolution:**
1. Check resource metrics
2. Identify memory leaks
3. Scale horizontally
4. Optimize resource usage

## Incident Communication Template

### Initial Alert (5 minutes)
```
🚨 INCIDENT: [Brief Description]
Severity: P[0-3]
Status: Investigating
Impact: [User impact description]
Sentry Link: [URL]
Lead: [Name]
```

### Update Template (every 30 min)
```
📊 UPDATE: [Incident Name]
Status: [Investigating/Mitigating/Resolved]
Timeline:
- [Time]: [Action taken]
- [Time]: [Finding]
Next Steps: [What's happening next]
ETA: [If known]
```

### Resolution Template
```
✅ RESOLVED: [Incident Name]
Duration: [Start] - [End]
Root Cause: [Brief explanation]
Resolution: [What fixed it]
Follow-up: [Action items]
Postmortem: [Link when available]
```

## Postmortem Checklist

### Information to Gather from Sentry
```
□ First occurrence timestamp
□ Total event count
□ Unique users affected
□ Error distribution by browser/OS/region
□ Stack trace and breadcrumbs
□ Associated release/commits
□ Time to detection
□ Time to resolution
```

### Postmortem Template
```markdown
# Incident Postmortem: [Title]

## Summary
[1-2 sentence description]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | First error in Sentry |
| HH:MM | Alert triggered |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Fix deployed |
| HH:MM | Confirmed resolved |

## Root Cause
[Technical explanation]

## Impact
- Users affected: X
- Duration: X minutes
- Revenue impact: $X (if applicable)

## Action Items
- [ ] [Preventive measure 1]
- [ ] [Preventive measure 2]
- [ ] [Monitoring improvement]
```

## Resources
- [Sentry Issue Details](https://docs.sentry.io/product/issues/issue-details/)
- [Sentry Alerts](https://docs.sentry.io/product/alerts/)
