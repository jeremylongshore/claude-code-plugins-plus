---
name: vercel-advanced-troubleshooting
description: |
  Execute apply Vercel advanced debugging techniques for hard-to-diagnose issues.
  Use when standard troubleshooting fails, investigating complex race conditions,
  or preparing evidence bundles for Vercel support escalation.
  Trigger with phrases like "vercel hard bug", "vercel mystery error",
  "vercel impossible to debug", "difficult vercel issue", "vercel deep debug".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Advanced Troubleshooting

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
- [Vercel Support Portal](https://support.vercel.com)
- [Vercel Status Page](https://www.vercel-status.com)
