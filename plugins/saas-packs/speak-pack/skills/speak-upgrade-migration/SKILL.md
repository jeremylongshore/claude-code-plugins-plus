---
name: speak-upgrade-migration
description: |
  Analyze, plan, and execute Speak SDK upgrades with breaking change detection.
  Use when upgrading Speak SDK versions, detecting deprecations,
  or migrating to new API versions for language learning features.
  Trigger with phrases like "upgrade speak", "speak migration",
  "speak breaking changes", "update speak SDK", "analyze speak version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Upgrade Migration

## Overview
Guide for upgrading Speak SDK versions and handling breaking changes in language learning integrations.

## Prerequisites
- Current Speak SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions
1. **Deprecation Handling**
2. **Rollback Procedure**
3. **Testing Upgrade in Staging**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Updated SDK version
- Fixed breaking changes
- Passing test suite
- Documented rollback procedure

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Import errors | Path changed | Update import paths |
| Type errors | Interface changed | Update type definitions |
| Runtime errors | API behavior changed | Review changelog |
| Test failures | Mock outdated | Update test mocks |

## Resources
- [Speak Changelog](https://github.com/speak/language-sdk/releases)
- [Speak Migration Guide](https://developer.speak.com/docs/migration)
- [Speak API Versioning](https://developer.speak.com/docs/versioning)

## Next Steps
For CI integration during upgrades, see `speak-ci-integration`.

## Examples

**Basic usage**: Apply speak upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize speak upgrade migration for production environments with multiple constraints and team-specific requirements.