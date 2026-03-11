---
name: supabase-incident-runbook
description: |
  Execute Supabase incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Supabase-related outages, investigating errors,
  or running post-incident reviews for Supabase integration failures.
  Trigger with phrases like "supabase incident", "supabase outage",
  "supabase down", "supabase on-call", "supabase emergency", "supabase broken".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Supabase Incident Runbook

## Prerequisites
- Access to Supabase dashboard and status page
- kubectl access to production cluster
- Prometheus/Grafana access
- Communication channels (Slack, PagerDuty)

## Instructions

### Step 1: Quick Triage
Run the triage commands to identify the issue source.

### Step 2: Follow Decision Tree
Determine if the issue is Supabase-side or internal.

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
- [Supabase Status Page](https://status.supabase.com)
- [Supabase Support](https://support.supabase.com)

## Overview

Execute Supabase incident response procedures with triage, mitigation, and postmortem.