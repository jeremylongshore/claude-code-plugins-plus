---
name: sentry-incident-runbook
description: |
  Manage incident response procedures using Sentry.
  Use when investigating production issues, triaging errors,
  or creating incident response workflows.
  Trigger with phrases like "sentry incident response", "sentry triage",
  "investigate sentry error", "sentry runbook".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Incident Runbook

## Prerequisites

- Sentry account with access to project issues
- Alert rules configured for critical errors
- Team notification channels set up (Slack, PagerDuty)
- Understanding of error severity classification

## Instructions

1. Check Sentry dashboard for active incidents and error spikes
2. Classify incident severity using P0-P3 framework based on error rate and user impact
3. Complete initial triage checklist to assess scope and gather context
4. Use Sentry API commands to retrieve issue details and recent events
5. Identify error pattern (deployment-related, third-party failure, data corruption, resource exhaustion)
6. Apply appropriate resolution steps based on identified pattern
7. Communicate status using incident templates (initial alert, updates, resolution)
8. Document findings and complete postmortem checklist after resolution

## Output
- Incident severity classification
- Triage checklists completed
- Root cause documented
- Resolution timeline recorded
- Postmortem report generated

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Issue Details](https://docs.sentry.io/product/issues/issue-details/)
- [Sentry Alerts](https://docs.sentry.io/product/alerts/)

## Overview

Manage incident response procedures using Sentry.