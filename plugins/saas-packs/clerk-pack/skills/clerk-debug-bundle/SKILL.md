---
name: clerk-debug-bundle
description: |
  Collect comprehensive debug information for Clerk issues.
  Use when troubleshooting complex problems, preparing support tickets,
  or diagnosing intermittent issues.
  Trigger with phrases like "clerk debug", "clerk diagnostics",
  "clerk support ticket", "clerk troubleshooting".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Debug Bundle

## Overview
Collect all necessary debug information for Clerk troubleshooting and support.

## Prerequisites
- Clerk SDK installed
- Access to application logs
- Browser with developer tools

## Instructions
- Step 1: Environment Debug Script
- Step 2: Runtime Health Check
- Step 3: Client-Side Debug Component
- Step 4: Request Debug Middleware
- Step 5: Generate Support Bundle

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Environment debug information
- Runtime health check endpoint
- Client-side debug panel
- Support bundle script

## Error Handling
| Issue | Debug Action |
|-------|--------------|
| Auth not working | Check /api/clerk-health endpoint |
| Token issues | Use debug panel to inspect token |
| Middleware problems | Enable CLERK_DEBUG=true |
| Session issues | Check session state in debug panel |

## Resources
- [Clerk Support](https://clerk.com/support)
- [Clerk Discord](https://clerk.com/discord)
- [GitHub Issues](https://github.com/clerk/javascript/issues)

## Next Steps
Proceed to `clerk-rate-limits` for understanding Clerk rate limits.
