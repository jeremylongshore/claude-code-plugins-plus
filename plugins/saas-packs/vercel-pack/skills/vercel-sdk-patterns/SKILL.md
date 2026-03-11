---
name: vercel-sdk-patterns
description: |
  Execute apply production-ready Vercel SDK patterns for TypeScript and Python.
  Use when implementing Vercel integrations, refactoring SDK usage,
  or establishing team coding standards for Vercel.
  Trigger with phrases like "vercel SDK patterns", "vercel best practices",
  "vercel code patterns", "idiomatic vercel".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vercel Sdk Patterns

## Prerequisites
- Completed `vercel-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Type-safe client singleton
- Robust error handling with structured logging
- Automatic retry with exponential backoff
- Runtime validation for API responses

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel SDK Reference](https://vercel.com/docs/sdk)
- [Vercel API Types](https://vercel.com/docs/types)
- [Zod Documentation](https://zod.dev/)

## Overview

Execute apply production-ready Vercel SDK patterns for TypeScript and Python.

## Instructions

1. Assess the current state of the Python configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference