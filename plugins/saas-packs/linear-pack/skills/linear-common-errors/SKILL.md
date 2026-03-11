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
- Error Categories
- Diagnostic Commands
- Error Handling Pattern

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Linear API Error Reference](https://developers.linear.app/docs/graphql/errors)
- [Rate Limiting Guide](https://developers.linear.app/docs/graphql/rate-limiting)
- [Authentication Guide](https://developers.linear.app/docs/graphql/authentication)

## Next Steps
Set up comprehensive debugging with `linear-debug-bundle`.
