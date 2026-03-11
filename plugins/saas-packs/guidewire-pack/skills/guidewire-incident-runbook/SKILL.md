---
name: guidewire-incident-runbook
description: |
  Incident response runbook for Guidewire InsuranceSuite production incidents.
  Use when responding to production issues, outages, or degraded performance.
  Trigger with phrases like "guidewire incident", "production issue",
  "outage response", "incident runbook", "troubleshooting guidewire".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Guidewire Incident Runbook

## Overview
Production incident response procedures for Guidewire InsuranceSuite including triage, diagnosis, resolution, and post-incident review.

## Prerequisites
- Service configured and accessible

## Instructions

### Step 1: Incident Severity Levels
Implement incident severity levels.
### Step 2: Incident Response Flow
┌─────────────────────────────────────────────────────────────────────────────────┐
### Step 3: Common Incident Scenarios
**Symptoms:**
### Step 4: Incident Communication Templates
INCIDENT: [Brief Description]
### Step 5: Post-Incident Review Template
Implement post-incident review template.
### Step 6: Incident Summary
Implement incident summary.
### Step 7: Timeline
Implement timeline.
### Step 8: Root Cause
[Detailed description of the root cause]

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Incident Severity Levels
- Incident Response Flow
- Common Incident Scenarios
- Incident Communication Templates
- Post-Incident Review Template
- Incident Summary

## Error Handling
| Issue | Solution |
|-------|----------|
| Configuration error | Check settings |

## Resources
- [Guidewire Support Portal](https://support.guidewire.com)
- [Guidewire Status Page](https://status.guidewire.com)
- [Guidewire Cloud Console](https://gcc.guidewire.com)

## Next Steps
For data handling procedures, see `guidewire-data-handling`.
