---
name: juicebox-debug-bundle
description: |
  Collect Juicebox debug evidence for support.
  Use when creating support tickets, gathering diagnostic info,
  or preparing error reports for Juicebox support team.
  Trigger with phrases like "juicebox debug info", "juicebox support bundle",
  "collect juicebox diagnostics", "juicebox troubleshooting".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox Debug Bundle

## Overview
Collect comprehensive diagnostic information for Juicebox support tickets.

## Prerequisites
- Access to application logs
- Juicebox API key configured
- Terminal access

## Instructions
- Step 1: Collect Environment Info
- Step 2: Test API Connectivity
- Step 3: Gather Error Logs
- Step 4: Create Support Bundle

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- `debug-bundle.txt` - Text summary
- `debug-bundle-*.json` - Structured data
- Filtered error logs
- API connectivity results

## Resources
- [Support Portal](https://juicebox.ai/support)
- [Community Forum](https://community.juicebox.ai)

## Next Steps
After collecting debug info, check `juicebox-rate-limits` for quota issues.
