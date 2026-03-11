---
name: clay-incident-runbook
description: |
  Execute Clay incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Clay-related outages, investigating errors,
  or running post-incident reviews for Clay integration failures.
  Trigger with phrases like "clay incident", "clay outage",
  "clay down", "clay on-call", "clay emergency", "clay broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Incident Runbook

## Overview

Rapid incident response procedures for Clay-related outages.

## Prerequisites

- Access to Clay dashboard and status page
- kubectl access to production cluster
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | Clay API unreachable |
| P2 | Degraded service | < 1 hour | High latency, partial failures |
| P3 | Minor impact | < 4 hours | Webhook delays, non-critical errors |
| P4 | No user impact | Next business day | Monitoring gaps |

## Instructions

### Step 1: Quick Triage

Check Clay status page, your integration health endpoint, error rate metrics, and recent pod logs.

### Step 2: Follow Decision Tree

If Clay API returns errors and status.clay.com shows an incident, wait and enable fallback. If no Clay incident, check your credentials and config. If no API errors but your service is unhealthy, investigate infrastructure.

### Step 3: Execute Immediate Actions

- **401/403**: Verify API key in secrets, update if rotated, restart pods
- **429**: Check rate limit headers, enable request queuing
- **500/503**: Enable graceful degradation, monitor Clay status

### Step 4: Communicate Status

Post to internal Slack with severity, impact, current action, and next update time. Update external status page with user-facing impact description.

For complete triage scripts, remediation commands, communication templates, and postmortem template, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Issue identified and categorized
- Remediation applied
- Stakeholders notified
- Evidence collected for postmortem

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status page | Network issue | Use mobile or VPN |
| kubectl fails | Auth expired | Re-authenticate |
| Metrics unavailable | Prometheus down | Check backup metrics |
| Secret rotation fails | Permission denied | Escalate to admin |

## Resources

- [Clay Status Page](https://status.clay.com)
- [Clay Support](https://support.clay.com)

## Next Steps

For data handling, see `clay-data-handling`.
