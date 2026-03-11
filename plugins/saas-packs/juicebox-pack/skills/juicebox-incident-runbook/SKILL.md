---
name: juicebox-incident-runbook
description: |
  Execute Juicebox incident response procedures.
  Use when responding to production incidents, troubleshooting outages,
  or following incident management protocols.
  Trigger with phrases like "juicebox incident", "juicebox outage",
  "juicebox down", "juicebox emergency".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Incident Runbook

## Overview
Standardized incident response procedures for Juicebox integration issues.

## Instructions
1. Quick Diagnostics
2. Incident Triage Decision Tree
3. Response Procedures
4. When Juicebox is Down
5. When Authentication Fails
6. When Rate Limited
7. When Requests Timeout
8. Incident Communication Template
9. Incident Report Template
10. On-Call Checklist
11. On-Call Handoff Checklist

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Diagnostic scripts
- Response procedures
- Communication templates
- On-call checklists

## Resources
- [Juicebox Status](https://status.juicebox.ai)
- [Support Portal](https://juicebox.ai/support)

## Next Steps
After incident, see `juicebox-data-handling` for data management.

## Prerequisites

- Access to the Juicebox Incident Runbook environment or API
- Required CLI tools installed and authenticated
- Familiarity with Juicebox Incident Runbook concepts and terminology

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Juicebox Incident Runbook |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox incident runbook to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox incident runbook for production environments with multiple constraints and team-specific requirements.