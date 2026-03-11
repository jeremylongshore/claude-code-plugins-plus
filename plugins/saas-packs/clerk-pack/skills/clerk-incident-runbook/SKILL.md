---
name: clerk-incident-runbook
description: |
  Incident response procedures for Clerk authentication issues.
  Use when handling auth outages, security incidents,
  or production authentication problems.
  Trigger with phrases like "clerk incident", "clerk outage",
  "clerk down", "auth not working", "clerk emergency".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Incident Runbook

## Overview
Procedures for responding to Clerk-related incidents in production.

## Prerequisites
- Access to Clerk dashboard
- Access to application logs
- Emergency contact list
- Rollback procedures documented

## Instructions
1. Incident Categories
2. Runbook Procedures
3. Emergency Contacts
4. Post-Incident
5. Lessons Learned

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Incident response procedures
- Recovery scripts
- Emergency bypass capability
- Post-incident templates

## Resources
- [Clerk Status](https://status.clerk.com)
- [Clerk Support](https://clerk.com/support)
- [Clerk Discord](https://clerk.com/discord)

## Next Steps
- **Date:** YYYY-MM-DD

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with security |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply clerk incident runbook to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk incident runbook for production environments with multiple constraints and team-specific requirements.