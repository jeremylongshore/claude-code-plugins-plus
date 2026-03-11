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
- Error Reference
- Diagnostic Commands
- Error Handling Pattern

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Error Codes Reference](https://juicebox.ai/docs/errors)
- [Status Page](https://status.juicebox.ai)

## Next Steps
After resolving errors, see `juicebox-debug-bundle` for collecting diagnostic info.
