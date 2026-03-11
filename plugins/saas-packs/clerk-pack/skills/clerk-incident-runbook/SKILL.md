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
- Incident Categories
- Runbook Procedures
- Emergency Contacts
- Post-Incident
- Lessons Learned

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
