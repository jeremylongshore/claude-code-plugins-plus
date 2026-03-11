---
name: vercel-upgrade-migration
description: |
  Execute analyze, plan, and execute Vercel SDK upgrades with breaking change detection.
  Use when upgrading Vercel SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade vercel", "vercel migration",
  "vercel breaking changes", "update vercel SDK", "analyze vercel version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Upgrade Migration

## Prerequisites
- Current Vercel SDK installed
- Git for version control
- Test suite available
- Staging environment


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Updated SDK version
- Fixed breaking changes
- Passing test suite
- Documented rollback procedure

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Changelog](https://github.com/vercel/vercel/releases)
- [Vercel Migration Guide](https://vercel.com/docs/migration)
