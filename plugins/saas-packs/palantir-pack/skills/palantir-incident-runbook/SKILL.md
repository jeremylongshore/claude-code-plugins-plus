---
name: palantir-incident-runbook
description: |
  Execute Palantir Foundry incident response with triage, mitigation, and postmortem.
  Use when responding to Foundry-related outages, API failures,
  or build pipeline incidents.
  Trigger with phrases like "palantir incident", "foundry outage",
  "palantir down", "foundry emergency", "palantir broken".
allowed-tools: Read, Grep, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, incident, runbook]
compatible-with: claude-code, codex, openclaw
---

# Palantir Incident Runbook

## Overview
Rapid incident response for Foundry-related outages: API failures, transform build failures, authentication issues, and data pipeline stalls.

## Prerequisites
- Access to application logs and Foundry build history
- Foundry service user credentials for health checks
- On-call escalation path defined

## Instructions

### Step 1: Triage (First 5 Minutes)
```bash
set -euo pipefail
echo "=== Foundry Incident Triage ==="
echo "Time: $(date -u)"

# 1. Check if Foundry itself is down
curl -s -o /dev/null -w "Foundry API: HTTP %{http_code}\n" \
  -H "Authorization: Bearer $FOUNDRY_TOKEN" \
  "https://$FOUNDRY_HOSTNAME/api/v2/ontologies" || echo "FOUNDRY UNREACHABLE"

# 2. Check our app health
curl -s http://localhost:8080/health | python -m json.tool

# 3. Check recent error logs
grep -c "ApiError\|status_code.*[45][0-9][0-9]" /var/log/app/app.log | tail -1
```

### Step 2: Classify Severity
| Severity | Criteria | Response Time |
|----------|----------|---------------|
| P1 Critical | Foundry API completely unreachable, all operations failing | Immediate |
| P2 High | Intermittent 429/5xx errors, degraded performance | 15 minutes |
| P3 Medium | Single transform failing, non-critical pipeline stalled | 1 hour |
| P4 Low | Deprecation warnings, performance degradation | Next business day |

### Step 3: Common Incident Playbooks

**Playbook A: Authentication Failure (401/403)**
```bash
# 1. Verify token is set
echo "Token set: ${FOUNDRY_TOKEN:+yes}"
echo "Token length: ${#FOUNDRY_TOKEN}"

# 2. Test with a fresh token
python -c "
import os, foundry
client = foundry.FoundryClient(
    auth=foundry.UserTokenAuth(
        hostname=os.environ['FOUNDRY_HOSTNAME'],
        token=os.environ['FOUNDRY_TOKEN'],
    ),
    hostname=os.environ['FOUNDRY_HOSTNAME'],
)
print('Auth OK:', list(client.ontologies.Ontology.list())[0].api_name)
"
# 3. If still failing: regenerate credentials in Developer Console
```

**Playbook B: Rate Limiting (429)**
```bash
# 1. Check rate limit headers from last response
# 2. Enable request throttling
# 3. Review batch operations for unnecessary API calls
# See palantir-rate-limits for detailed implementation
```

**Playbook C: Transform Build Failure**
```text
1. Open Foundry > Pipeline Builder > failed build
2. Check the "Errors" tab for stack trace
3. Common causes:
   - OutOfMemoryError → add @configure(profile=["DRIVER_MEMORY_LARGE"])
   - AnalysisException → column name mismatch (case-sensitive)
   - Input dataset empty → check upstream pipeline
4. Fix code, commit, trigger rebuild
```

### Step 4: Escalation
```text
Level 1: On-call engineer (your team)
  → Check logs, verify credentials, restart service

Level 2: Platform team
  → Foundry enrollment issues, networking, VPN

Level 3: Palantir support
  → Create ticket with debug bundle (palantir-debug-bundle)
  → Include: error codes, timestamps, request IDs
```

### Step 5: Postmortem Template
```markdown
## Incident: [Title]
**Duration:** [start] to [end] ([X] minutes)
**Severity:** P[1-4]
**Impact:** [What was affected]

### Timeline
- HH:MM — Alert fired
- HH:MM — Investigation started
- HH:MM — Root cause identified
- HH:MM — Fix deployed
- HH:MM — Verified resolution

### Root Cause
[Description]

### Action Items
- [ ] [Preventive measure 1]
- [ ] [Preventive measure 2]
```

## Output
- Incident triaged and classified within 5 minutes
- Appropriate playbook executed
- Escalation if needed with debug bundle
- Postmortem documented with action items

## Error Handling
| Incident Type | First Action | Escalation Trigger |
|---------------|-------------|-------------------|
| API unreachable | Check Foundry status | If Foundry is up but we cannot connect |
| Auth failure | Test with fresh token | If new token also fails |
| Rate limiting | Enable throttling | If throttling does not resolve |
| Build failure | Check error logs | If error is infrastructure-related |

## Resources
- [Foundry Documentation](https://www.palantir.com/docs/foundry)
- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)

## Next Steps
For proactive monitoring, see `palantir-observability`.
