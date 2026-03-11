---
name: openevidence-incident-runbook
description: |
  Execute OpenEvidence incident response procedures with triage, mitigation, and postmortem.
  Use when responding to OpenEvidence-related outages, investigating errors,
  or running post-incident reviews for clinical AI integration failures.
  Trigger with phrases like "openevidence incident", "openevidence outage",
  "openevidence down", "openevidence emergency", "clinical ai broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Incident Runbook

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Rapid incident response procedures for OpenEvidence clinical AI integration outages in healthcare environments. Includes severity classification, triage steps, error-specific remediation, fallback procedures, and postmortem templates.

## Prerequisites
- Access to OpenEvidence status page
- kubectl access to production cluster
- Prometheus/Grafana access
- PagerDuty or on-call system access

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete outage | < 15 min | API unreachable, all queries failing |
| P2 | Degraded service | < 1 hour | High latency, partial failures |
| P3 | Minor impact | < 4 hours | DeepConsult delays, webhook issues |
| P4 | No user impact | Next business day | Alert noise, logging issues |

## Critical Note
OpenEvidence outages may affect clinical decision-making. Always communicate clearly with clinical staff, ensure fallback procedures are known, and document any clinical impact.

## Instructions

### Step 1: Initial Assessment (2 minutes)
Check OpenEvidence status page, your integration health endpoint, error rate metrics, and recent error logs.

### Step 2: Follow Decision Tree
- API errors + OpenEvidence status incident -> Enable fallback, wait for resolution
- API errors + no status incident -> Check credentials, config, network
- No API errors + unhealthy service -> Infrastructure issue (pods, memory, network)

### Step 3: Apply Error-Specific Remediation
- **401/403**: Verify API key, rotate if needed, restart pods
- **429**: Enable request queuing, contact OpenEvidence for limit increase
- **500/503**: Enable graceful degradation, notify clinical staff
- **Timeout**: Increase timeout temporarily, check network latency

### Step 4: Enable Fallback
Return helpful message directing to UpToDate, DynaMed, or clinical guidelines directly.

### Step 5: Communicate
Notify clinical staff via Slack/Teams and email. Update status page.

### Step 6: Post-Incident
Collect evidence (logs, metrics, alerts), run postmortem with clinical impact assessment, create action items.

## Output
- Quick triage procedure completed
- Issue identified and categorized
- Remediation applied
- Clinical staff notified
- Evidence collected for postmortem

## Error Handling
| Error Type | Quick Fix |
|------------|-----------|
| 401/403 Auth | `kubectl create secret` with new key, `kubectl rollout restart` |
| 429 Rate Limit | `kubectl set env RATE_LIMIT_MODE=queue` |
| 500/503 Server | `kubectl set env OPENEVIDENCE_FALLBACK=true` |
| Timeout | `kubectl set env OPENEVIDENCE_TIMEOUT=60000` |

## Examples

### One-Line Health Check
```bash
set -euo pipefail
curl -sf https://api.yourhealthcare.com/health/openevidence | jq '.status' || echo "UNHEALTHY"
```

### Enable/Disable Fallback
```bash
set -euo pipefail
kubectl set env deployment/clinical-evidence-api OPENEVIDENCE_FALLBACK=true   # Enable
kubectl set env deployment/clinical-evidence-api OPENEVIDENCE_FALLBACK=false  # Disable
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [OpenEvidence Status](https://status.openevidence.com/)
- [OpenEvidence Support](mailto:support@openevidence.com)