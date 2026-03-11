---
name: juicebox-common-errors
description: |
  Diagnose and fix Juicebox common errors.
  Use when encountering API errors, debugging integration issues,
  or troubleshooting Juicebox connection problems.
  Trigger with phrases like "juicebox error", "fix juicebox issue",
  "juicebox not working", "debug juicebox".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Common Errors

## Overview
Quick reference for diagnosing and resolving common Juicebox API errors.

## Instructions
1. Error Reference
2. Diagnostic Commands
3. Error Handling Pattern

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Error Codes Reference](https://juicebox.ai/docs/errors)
- [Status Page](https://status.juicebox.ai)

## Next Steps
After resolving errors, see `juicebox-debug-bundle` for collecting diagnostic info.

## Prerequisites

- Access to the debugging environment or API
- Required CLI tools installed and authenticated
- Familiarity with debugging concepts and terminology

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [debugging implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with debugging |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox common errors for production environments with multiple constraints and team-specific requirements.