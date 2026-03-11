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

See implementation guide for detailed steps.

For full implementation details and code examples, load:
`references/implementation-guide.md`

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
