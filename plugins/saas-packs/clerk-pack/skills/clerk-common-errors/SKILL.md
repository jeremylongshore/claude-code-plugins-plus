---
name: clerk-common-errors
description: |
  Troubleshoot common Clerk errors and issues.
  Use when encountering authentication errors, SDK issues,
  or configuration problems with Clerk.
  Trigger with phrases like "clerk error", "clerk not working",
  "clerk authentication failed", "clerk issue", "fix clerk".
allowed-tools: Read, Write, Edit, Grep, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Common Errors

## Overview
Diagnose and resolve common Clerk authentication errors and issues.

## Prerequisites
- Clerk SDK installed
- Access to Clerk dashboard for configuration checks
- Browser developer tools for debugging

## Instructions
- Error Category 1: Configuration Errors
- Error Category 2: Authentication Errors
- Error Category 3: Middleware Errors
- Error Category 4: Server/Client Errors
- Error Category 5: Webhook Errors

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Identified error category
- Root cause analysis
- Working solution code

## Resources
- [Clerk Error Codes](https://clerk.com/docs/errors/overview)
- [Debugging Guide](https://clerk.com/docs/debugging)
- [Discord Community](https://clerk.com/discord)

## Next Steps
Proceed to `clerk-debug-bundle` for comprehensive debugging tools.
