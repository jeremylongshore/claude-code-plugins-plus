---
name: sentry-sdk-patterns
description: |
  Execute best practices for using Sentry SDK in TypeScript and Python.
  Use when implementing error handling patterns, structuring Sentry code,
  or optimizing SDK usage.
  Trigger with phrases like "sentry best practices", "sentry patterns",
  "sentry sdk usage", "sentry code structure".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Sdk Patterns

## Prerequisites
- Sentry SDK installed and configured
- Understanding of error handling concepts
- Familiarity with async/await patterns

## Instructions

1. Create a centralized error handler module for consistent error capture
2. Implement scoped context for transactions and operations
3. Add structured breadcrumbs for debugging context
4. Configure error boundaries in frameworks (React, Vue, etc.)
5. Use custom fingerprinting for better issue grouping
6. Implement async error handling with proper scope propagation
7. Add performance tracing for critical paths
8. Configure sampling rates based on traffic volume


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Clean, maintainable error handling code
- Consistent error context across application
- Efficient Sentry SDK usage

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry SDK Docs](https://docs.sentry.io/platforms/)
- [Sentry Best Practices](https://docs.sentry.io/product/issues/best-practices/)

## Overview

Execute best practices for using Sentry SDK in TypeScript and Python.