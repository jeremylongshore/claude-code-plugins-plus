---
name: supabase-advanced-troubleshooting
description: |
  Execute apply Supabase advanced debugging techniques for hard-to-diagnose issues.
  Use when standard troubleshooting fails, investigating complex race conditions,
  or preparing evidence bundles for Supabase support escalation.
  Trigger with phrases like "supabase hard bug", "supabase mystery error",
  "supabase impossible to debug", "difficult supabase issue", "supabase deep debug".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Supabase Advanced Troubleshooting

## Prerequisites
- Access to production logs and metrics
- kubectl access to clusters
- Network capture tools available
- Understanding of distributed tracing

## Instructions

### Step 1: Collect Evidence Bundle
Run the comprehensive debug script to gather all relevant data.

### Step 2: Systematic Isolation
Test each layer independently to identify the failure point.

### Step 3: Create Minimal Reproduction
Strip down to the simplest failing case.

### Step 4: Escalate with Evidence
Use the support template with all collected evidence.

## Output
- Comprehensive debug bundle collected
- Failure layer identified
- Minimal reproduction created
- Support escalation submitted

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase Support Portal](https://support.supabase.com)
- [Supabase Status Page](https://status.supabase.com)

## Overview

Execute apply Supabase advanced debugging techniques for hard-to-diagnose issues.