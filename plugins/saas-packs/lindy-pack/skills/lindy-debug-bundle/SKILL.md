---
name: lindy-debug-bundle
description: |
  Comprehensive debugging toolkit for Lindy AI agents.
  Use when investigating complex issues, collecting diagnostics,
  or preparing support tickets.
  Trigger with phrases like "lindy debug", "lindy diagnostics",
  "lindy support bundle", "investigate lindy issue".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Comprehensive debugging toolkit for collecting diagnostics and resolving issues.

## Prerequisites
- Lindy SDK installed
- Access to logs
- curl installed for API testing

## Instructions

### Step 1: Collect Environment Info
### Step 2: Test API Connectivity
### Step 3: Collect Agent State
### Step 4: Check Run History
### Step 5: Generate Support Bundle

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Environment diagnostic information
- API connectivity test results
- Agent state and configuration
- Run history analysis
- Exportable support bundle

## Error Handling
| Issue | Diagnostic | Resolution |
|-------|------------|------------|
| Auth fails | Check API key | Regenerate key |
| Timeout | Check network | Verify firewall |
| Agent missing | Check environment | Verify agent ID |

## Examples

### Quick Health Check
### Full Debug Script
## Resources
- [Lindy Support](https://support.lindy.ai)
- [Status Page](https://status.lindy.ai)
- [API Reference](https://docs.lindy.ai/api)

## Next Steps
Proceed to `lindy-rate-limits` for rate limit management.