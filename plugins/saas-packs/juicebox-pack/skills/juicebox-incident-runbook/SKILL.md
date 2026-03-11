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
- Quick Diagnostics
- Incident Triage Decision Tree
- Response Procedures
- When Juicebox is Down
- When Authentication Fails
- When Rate Limited
- When Requests Timeout
- Incident Communication Template
- Incident Report Template
- On-Call Checklist
- On-Call Handoff Checklist

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
