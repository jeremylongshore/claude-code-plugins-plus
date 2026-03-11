---
name: lindy-common-errors
description: |
  Troubleshoot common Lindy AI errors and issues.
  Use when encountering errors, debugging agent failures,
  or resolving integration problems.
  Trigger with phrases like "lindy error", "lindy not working",
  "debug lindy", "lindy troubleshoot".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Common Errors

## Overview
Comprehensive guide to troubleshooting common Lindy AI errors and issues.

## Prerequisites
- Lindy SDK installed
- Access to logs and error messages
- Basic debugging skills

## Common Errors

### Authentication Errors

#### LINDY_AUTH_INVALID_KEY
**Causes:**
- Expired API key
- Incorrect key format
- Key from wrong environment

**Solutions:**
### Rate Limit Errors

#### LINDY_RATE_LIMITED
**Causes:**
- Too many API requests
- Concurrent agent runs exceeded
- Burst limit reached

**Solutions:**
### Agent Errors

#### LINDY_AGENT_NOT_FOUND
**Solutions:**
#### LINDY_AGENT_TIMEOUT
**Solutions:**
### Tool Errors

#### LINDY_TOOL_FAILED
**Solutions:**
## Debugging Checklist


For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Error Code | HTTP Status | Retry? |
|------------|-------------|--------|
| LINDY_AUTH_INVALID_KEY | 401 | No |
| LINDY_RATE_LIMITED | 429 | Yes |
| LINDY_AGENT_NOT_FOUND | 404 | No |
| LINDY_AGENT_TIMEOUT | 504 | Yes |
| LINDY_TOOL_FAILED | 500 | Maybe |

## Resources
- [Lindy Error Reference](https://docs.lindy.ai/errors)
- [Status Page](https://status.lindy.ai)
- [Support](https://support.lindy.ai)

## Next Steps
Proceed to `lindy-debug-bundle` for comprehensive debugging.

## Instructions

1. Assess the current state of the debugging configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [debugging implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply lindy common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy common errors for production environments with multiple constraints and team-specific requirements.