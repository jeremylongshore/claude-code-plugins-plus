---
name: lokalise-common-errors
description: |
  Diagnose and fix Lokalise common errors and exceptions.
  Use when encountering Lokalise errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "lokalise error", "fix lokalise",
  "lokalise not working", "debug lokalise", "lokalise 401", "lokalise 429".
allowed-tools: Read, Grep, Bash(curl:*), Bash(lokalise2:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Common Errors

## Overview
Quick reference for the most common Lokalise API errors and their solutions.

## Prerequisites
- Lokalise SDK/CLI installed
- API token configured
- Access to error logs

## Instructions
1. **Quick Diagnostic Commands**
2. **Escalation Path**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Error | Solution |
|-------|----------|
| 401 Unauthorized - Invalid API Token | See implementation guide |
| 403 Forbidden - Insufficient Permissions | See implementation guide |
| 404 Not Found - Resource Missing | See implementation guide |
| 429 Too Many Requests - Rate Limited | See implementation guide |
| 400 Bad Request - Invalid Parameters | See implementation guide |
| 400 Key Limit Exceeded | See implementation guide |
| 413 Payload Too Large | See implementation guide |
| Upload Process Failed | See implementation guide |

## Resources
- [API Error Codes](https://developers.lokalise.com/reference/api-errors)
- [Lokalise Status](https://status.lokalise.com)
- [Community Forum](https://community.lokalise.com)

## Next Steps
For comprehensive debugging, see `lokalise-debug-bundle`.
