---
name: speak-common-errors
description: |
  Diagnose and fix Speak common errors and exceptions.
  Use when encountering Speak errors, debugging failed sessions,
  or troubleshooting language learning integration issues.
  Trigger with phrases like "speak error", "fix speak",
  "speak not working", "debug speak", "speak lesson failed".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Common Errors

## Overview
Quick reference for the top 10 most common Speak errors and their solutions.

## Prerequisites
- Speak SDK installed
- API credentials configured
- Access to error logs

## Instructions
1. **Quick Diagnostic Commands**
2. **Escalation Path**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Error | Solution |
|-------|----------|
| Authentication Failed | See implementation guide |
| Rate Limit Exceeded | See implementation guide |
| Audio Processing Failed | See implementation guide |
| Session Expired | See implementation guide |
| Language Not Supported | See implementation guide |
| Speech Recognition Failed | See implementation guide |
| Network Timeout | See implementation guide |
| Quota Exceeded | See implementation guide |

## Resources
- [Speak Status Page](https://status.speak.com)
- [Speak Support](https://support.speak.com)
- [Speak Error Codes](https://developer.speak.com/docs/errors)

## Next Steps
For comprehensive debugging, see `speak-debug-bundle`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [debugging implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply speak common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize speak common errors for production environments with multiple constraints and team-specific requirements.