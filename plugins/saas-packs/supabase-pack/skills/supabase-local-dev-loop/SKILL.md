---
name: supabase-local-dev-loop
description: |
  Configure Supabase local development with hot reload and testing.
  Use when setting up a development environment, configuring test workflows,
  or establishing a fast iteration cycle with Supabase.
  Trigger with phrases like "supabase dev setup", "supabase local development",
  "supabase dev environment", "develop with supabase".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Local Dev Loop

## Prerequisites
- Completed `supabase-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support
- Git for version control


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Working development environment with hot reload
- Configured test suite with mocking
- Environment variable management
- Fast iteration cycle for Supabase development

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase SDK Reference](https://supabase.com/docs/sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/esbuild-kit/tsx)
