---
name: documenso-incident-runbook
description: |
  Incident response procedures for Documenso integration issues.
  Use when diagnosing production incidents, handling outages,
  or responding to Documenso service disruptions.
  Trigger with phrases like "documenso incident", "documenso outage",
  "documenso down", "documenso troubleshooting".
allowed-tools: Read, Bash(curl:*), Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Documenso Incident Runbook

## Overview
Step-by-step procedures for responding to Documenso integration incidents.

## Prerequisites
- Access to monitoring dashboards
- kubectl access (if using Kubernetes)
- Documenso dashboard access
- On-call escalation contacts

## Instructions

### Step 1: Incident Severity Levels
Implement incident severity levels.
### Step 2: Quick Diagnostic Commands
curl -s https://status.documenso.com/api/v2/status.json | jq '.status'
### Step 3: Incident Response Procedures
**Symptoms:**
### Step 4: Circuit Breaker Implementation
// Emergency circuit breaker
### Step 5: Post-Incident Review Template
Implement post-incident review template.
### Step 6: Incident Report: [Title]
**Date:** YYYY-MM-DD
### Step 7: Emergency Contacts
Implement emergency contacts.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Incident Severity Levels
- Quick Diagnostic Commands
- Incident Response Procedures
- Circuit Breaker Implementation
- Post-Incident Review Template
- Incident Report: [Title]

## Error Handling
| Issue | Solution |
|-------|----------|
| Configuration error | Check settings |

## Resources
- [Documenso Status](https://status.documenso.com)
- [Documenso Support](mailto:support@documenso.com)
- [Internal Wiki - Signing Service]

## Next Steps
For data handling procedures, see `documenso-data-handling`.
