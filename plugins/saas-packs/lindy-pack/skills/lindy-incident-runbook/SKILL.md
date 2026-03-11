---
name: lindy-incident-runbook
description: |
  Incident response runbook for Lindy AI integrations.
  Use when responding to incidents, troubleshooting outages,
  or creating on-call procedures.
  Trigger with phrases like "lindy incident", "lindy outage",
  "lindy on-call", "lindy runbook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Incident Runbook

## Overview
Incident response procedures for Lindy AI integration issues.

## Prerequisites
- Access to Lindy dashboard
- Monitoring dashboards available
- Escalation contacts known
- Admin access to production

## Incident Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| SEV1 | Complete outage | 15 minutes | All agents failing |
| SEV2 | Partial outage | 30 minutes | One critical agent down |
| SEV3 | Degraded | 2 hours | High latency, some errors |
| SEV4 | Minor | 24 hours | Cosmetic issues |


For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Quick Diagnostics

### Step 1: Check Lindy Status
### Step 2: Verify Authentication
### Step 3: Check Rate Limits
## Common Incidents

### Incident: Complete API Outage

**Symptoms:**
- All API calls failing
- 5xx errors from Lindy

**Runbook:**
**Fallback Code:**
### Incident: Rate Limiting

**Symptoms:**
- 429 errors
- "Rate limit exceeded" messages

**Runbook:**
**Throttling Code:**
### Incident: Agent Failures

**Symptoms:**
- Specific agent not responding
- Unexpected outputs
- Timeout errors

**Runbook:**
**Diagnostic Script:**
### Incident: High Latency

**Symptoms:**
- Response times > 10 seconds
- Timeouts increasing

**Runbook:**
## Escalation Matrix

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | Initial response |
| L2 | Engineering lead | After 30 min SEV1/2 |
| L3 | VP Engineering | After 1 hour SEV1 |
| Lindy | support@lindy.ai | External issue confirmed |

## Post-Incident

### Incident Report Template
## Output
- Quick diagnostic commands
- Common incident runbooks
- Fallback code patterns
- Escalation procedures
- Post-incident template

## Resources
- [Lindy Status](https://status.lindy.ai)
- [Lindy Support](https://support.lindy.ai)
- [API Reference](https://docs.lindy.ai/api)

## Next Steps
Proceed to `lindy-data-handling` for data management.

## Instructions

1. Assess the current state of the Lindy Incident Runbook configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Lindy Incident Runbook |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply lindy incident runbook to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy incident runbook for production environments with multiple constraints and team-specific requirements.