---
name: linear-common-errors
description: |
  Diagnose and fix common Linear API errors.
  Use when encountering Linear API errors, debugging integration issues,
  or troubleshooting authentication problems.
  Trigger with phrases like "linear error", "linear API error",
  "debug linear", "linear not working", "linear authentication error".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Common Errors

## Overview
Quick reference for diagnosing and resolving common Linear API errors.

## Prerequisites
- Linear SDK or API access configured
- Access to application logs
- Understanding of HTTP status codes

## Instructions
1. Error Categories
2. Diagnostic Commands
3. Error Handling Pattern

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Linear API Error Reference](https://developers.linear.app/docs/graphql/errors)
- [Rate Limiting Guide](https://developers.linear.app/docs/graphql/rate-limiting)
- [Authentication Guide](https://developers.linear.app/docs/graphql/authentication)

## Next Steps
Set up comprehensive debugging with `linear-debug-bundle`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [authentication implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with authentication |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply linear common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear common errors for production environments with multiple constraints and team-specific requirements.