---
name: twinmind-incident-runbook
description: |
  Incident response procedures for TwinMind integration failures.
  Use when experiencing outages, debugging production issues,
  or responding to alerts related to TwinMind.
  Trigger with phrases like "twinmind incident", "twinmind outage",
  "twinmind down", "twinmind emergency", "twinmind runbook".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# TwinMind Incident Runbook

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Procedures for diagnosing and resolving TwinMind integration incidents, covering classification, diagnostics, common scenarios, escalation, and post-incident review.

## Prerequisites
- Access to monitoring dashboards
- Production environment credentials
- On-call rotation contacts
- TwinMind support contact

## Instructions

### Step 1: Classify and Acknowledge
Classify severity (P1=15min/P2=1hr/P3=4hr/P4=24hr). Acknowledge in PagerDuty, join incident Slack channel, note start time.

### Step 2: Run Quick Health Checks
Check TwinMind status page, your service health endpoint, recent deployments, and infrastructure status using diagnostic commands.

### Step 3: Diagnose by Scenario
Follow scenario-specific playbooks: all transcriptions failing (API down, invalid key, network issue), high latency (TwinMind slow, service overloaded, network latency), rate limiting (429 errors, heavy consumers), or authentication failures (401 errors, key rotation).

### Step 4: Execute Resolution
Apply resolution steps based on diagnosis. Follow escalation path: On-Call (0-15min) -> Team Lead (15-30min) -> Engineering Manager (30-60min) -> VP Engineering (60+ min).

### Step 5: Post-Incident Review
Confirm resolution, update status page, notify stakeholders, document timeline, schedule post-mortem within 1 week, create action items.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for diagnostic commands, scenario playbooks, and incident report template.

## Output
- Incident classification guide
- Diagnostic commands
- Common scenario playbooks
- Escalation procedures
- Post-incident checklist
- Report template

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| All transcriptions failing | TwinMind API down | Monitor status.twinmind.com, notify users |
| High latency (P95 > 5s) | Service overloaded | Scale replicas, queue requests |
| Rate limit exceeded (429) | Too many requests | Enable request queue, request limit increase |
| Auth failures (401) | Key expired/revoked | Regenerate key, update secrets |

## Examples
```bash
# Quick health check
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health

# Check recent errors
kubectl logs -l app=twinmind-service --tail=100 | grep -i error

# Check rate limit status
curl -I -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health 2>/dev/null | grep -i ratelimit
```

## Resources
- [TwinMind Status Page](https://status.twinmind.com)
- [TwinMind Support](https://twinmind.com/support)
- [PagerDuty Best Practices](https://response.pagerduty.com/)

## Next Steps
For data handling procedures, see `twinmind-data-handling`.
