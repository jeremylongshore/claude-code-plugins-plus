---
name: supabase-upgrade-migration
description: |
  Execute analyze, plan, and execute Supabase SDK upgrades with breaking change detection.
  Use when upgrading Supabase SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade supabase", "supabase migration",
  "supabase breaking changes", "update supabase SDK", "analyze supabase version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Upgrade Migration

## Prerequisites
- Current Supabase SDK installed
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
- [Supabase Changelog](https://github.com/supabase/sdk/releases)
- [Supabase Migration Guide](https://supabase.com/docs/migration)
