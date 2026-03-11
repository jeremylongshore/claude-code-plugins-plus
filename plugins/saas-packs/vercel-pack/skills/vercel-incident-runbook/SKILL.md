---
name: vercel-incident-runbook
description: |
  Execute Vercel incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Vercel-related outages, investigating errors,
  or running post-incident reviews for Vercel integration failures.
  Trigger with phrases like "vercel incident", "vercel outage",
  "vercel down", "vercel on-call", "vercel emergency", "vercel broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vercel Incident Runbook

## Prerequisites
- Access to Vercel dashboard and status page
- kubectl access to production cluster
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Instructions

### Step 1: Quick Triage
Run the triage commands to identify the issue source.

### Step 2: Follow Decision Tree
Determine if the issue is Vercel-side or internal.

### Step 3: Execute Immediate Actions
Apply the appropriate remediation for the error type.

### Step 4: Communicate Status
Update internal and external stakeholders.

## Output
- Issue identified and categorized
- Remediation applied
- Stakeholders notified
- Evidence collected for postmortem

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Status Page](https://www.vercel-status.com)
- [Vercel Support](https://support.vercel.com)

## Overview

Execute Vercel incident response procedures with triage, mitigation, and postmortem.