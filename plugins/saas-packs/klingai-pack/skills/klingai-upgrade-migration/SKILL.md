---
name: klingai-upgrade-migration
description: |
  Execute migrate and upgrade Kling AI SDK versions safely. Use when updating dependencies or migrating
  configurations. Trigger with phrases like 'klingai upgrade', 'kling ai migration',
  'update klingai', 'klingai breaking changes'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview

This skill guides you through SDK version upgrades, API migrations, configuration changes, and handling breaking changes safely in Kling AI integrations.

## Prerequisites

- Existing Kling AI integration
- Version control for rollback capability
- Test environment available

## Instructions

Follow these steps for safe upgrades:

1. **Review Changes**: Check release notes for breaking changes
2. **Update Dependencies**: Upgrade SDK packages
3. **Update Code**: Adapt to API changes
4. **Test Thoroughly**: Validate all functionality
5. **Deploy Gradually**: Use canary or blue-green deployment

## Output

Successful execution produces:
- Updated SDK and dependencies
- Migrated configuration
- Updated code patterns
- Verified functionality
- Rollback capability if needed

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Changelog](https://docs.klingai.com/changelog)
- [Migration Guide](https://docs.klingai.com/migration)
- [API Versioning](https://docs.klingai.com/versioning)