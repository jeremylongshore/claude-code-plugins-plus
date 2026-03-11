---
name: evernote-incident-runbook
description: |
  Incident response runbook for Evernote integration issues.
  Use when troubleshooting production incidents, handling outages,
  or responding to Evernote service issues.
  Trigger with phrases like "evernote incident", "evernote outage",
  "evernote emergency", "troubleshoot evernote production".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Incident Runbook

## Overview
Step-by-step procedures for responding to Evernote integration incidents including outages, rate limits, authentication failures, and data issues.

## Prerequisites
- Access to monitoring dashboards
- Production logs access
- Evernote API credentials
- Communication channels for escalation

## Instructions

1. See implementation guide for detailed steps.

2. For full implementation details and code examples, load:
3. `references/implementation-guide.md`

## Output
- Incident classification guide
- Step-by-step response procedures
- Diagnostic scripts
- Mitigation strategies
- Communication templates
- Post-incident checklist

## Resources
- [Evernote Status Page](https://status.evernote.com/)
- [Evernote Developer Support](https://dev.evernote.com/support/)
- [Error Handling](https://dev.evernote.com/doc/articles/error_handling.php)

## Next Steps
For data handling best practices, see `evernote-data-handling`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Evernote Incident Runbook |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote incident runbook to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote incident runbook for production environments with multiple constraints and team-specific requirements.