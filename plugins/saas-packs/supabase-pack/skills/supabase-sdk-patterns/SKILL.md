---
name: supabase-sdk-patterns
description: |
  Execute apply production-ready Supabase SDK patterns for TypeScript and Python.
  Use when implementing Supabase integrations, refactoring SDK usage,
  or establishing team coding standards for Supabase.
  Trigger with phrases like "supabase SDK patterns", "supabase best practices",
  "supabase code patterns", "idiomatic supabase".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Sdk Patterns

## Prerequisites
- Completed `supabase-install-auth` setup
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
- [Supabase SDK Reference](https://supabase.com/docs/sdk)
- [Supabase API Types](https://supabase.com/docs/types)
- [Zod Documentation](https://zod.dev/)
