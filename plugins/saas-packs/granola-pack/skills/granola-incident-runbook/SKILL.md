---
name: granola-incident-runbook
description: |
  Incident response procedures for Granola meeting capture issues.
  Use when handling meeting capture failures, system outages,
  or urgent troubleshooting situations.
  Trigger with phrases like "granola incident", "granola outage",
  "granola emergency", "granola not recording", "granola down".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Granola Incident Runbook

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Standard operating procedures for responding to Granola incidents and meeting capture failures, from recording issues to complete outages.

## Prerequisites
- Granola admin access
- Knowledge of incident severity levels
- Communication channels identified

## Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P1 | Critical | < 15 min | Complete outage, data loss |
| P2 | High | < 1 hour | Recording failures, sync issues |
| P3 | Medium | < 4 hours | Single user issues |
| P4 | Low | < 24 hours | UI bugs |

## Instructions

### Step 1: Assess Severity
Check status page (`status.granola.ai`), determine scope (single user vs org-wide), classify severity.

### Step 2: Quick Fix by Incident Type
- **Not Recording**: Click Start Recording, check calendar/audio permissions, restart app
- **No Audio**: Check input device, test mic, restart app
- **Processing Stuck**: Wait 15 min, check connectivity, restart app
- **Integration Failure**: Reconnect integration, check destination permissions
- **Complete Outage**: Enable backup note-taking, monitor status page

### Step 3: Communicate Status
Post to internal Slack with status, impact, workaround, and ETA. Update every 30 minutes.

### Step 4: Escalate if Needed
IT Support -> Granola Admin -> Team Lead -> VP/CTO (P1 only).

### Step 5: Post-Incident Review
Document timeline, root cause, resolution, and prevention steps.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for status check commands, detailed troubleshooting per incident type, communication templates, and post-incident report template.

## Output
- Incident classified and acknowledged
- Quick fix applied or workaround enabled
- Stakeholders notified with status updates
- Post-incident review documented

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Recording not starting | Calendar not synced | Reconnect calendar OAuth |
| Empty transcript | Mic not detected | Check System Preferences audio input |
| Notes not appearing | Processing queue delay | Wait 15 min, check status page |
| Integration broken | Token expired | Reconnect in Settings > Integrations |

## Examples

### Quick Status Check
```bash
curl -s https://status.granola.ai/api/v2/status.json | jq '.status'
```

## Resources
- [Granola Status](https://status.granola.ai)
- [Support Center](https://granola.ai/help)
- [Known Issues](https://granola.ai/updates)

## Next Steps
Proceed to `granola-data-handling` for data management procedures.
