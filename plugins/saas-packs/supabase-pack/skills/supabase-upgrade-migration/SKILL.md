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

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

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

## Overview

Execute analyze, plan, and execute Supabase SDK upgrades with breaking change detection.

## Instructions

1. Assess the current state of the migration configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference