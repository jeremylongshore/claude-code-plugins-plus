---
name: documenso-debug-bundle
description: |
  Comprehensive debugging toolkit for Documenso integrations.
  Use when troubleshooting complex issues, gathering diagnostic information,
  or creating support tickets for Documenso problems.
  Trigger with phrases like "debug documenso", "documenso diagnostics",
  "troubleshoot documenso", "documenso support ticket".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Comprehensive debugging tools and diagnostic scripts for Documenso integration issues.

## Prerequisites
- Documenso SDK installed
- Access to logs and configuration
- curl for API testing

## Instructions

### Step 1: Debug Scripts
// scripts/documenso-diagnostic.ts
### Step 2: curl Debug Commands
curl -v -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
### Step 3: Environment Checklist
echo "=== Documenso Environment Check ==="
### Step 4: Support Ticket Template
When creating a support ticket, include:
### Step 5: Documenso Support Request
[Describe what you expected vs what happened]

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Debug Scripts
- curl Debug Commands
- Environment Checklist
- Support Ticket Template
- Documenso Support Request

## Error Handling
| Issue | Solution |
|-------|----------|
| Configuration error | Check settings |

## Resources
- [Documenso GitHub Issues](https://github.com/documenso/documenso/issues)
- [Documenso Discord](https://documenso.com/discord)
- [API Status](https://status.documenso.com)

## Next Steps
For rate limit handling, see `documenso-rate-limits`.

## Examples

**Basic usage**: Apply documenso debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso debug bundle for production environments with multiple constraints and team-specific requirements.