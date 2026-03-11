---
name: juicebox-upgrade-migration
description: |
  Plan and execute Juicebox SDK upgrades.
  Use when upgrading SDK versions, migrating between API versions,
  or handling breaking changes.
  Trigger with phrases like "upgrade juicebox", "juicebox migration",
  "update juicebox SDK", "juicebox breaking changes".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Upgrade Migration

## Overview
Plan and execute safe Juicebox SDK version upgrades with minimal disruption.

## Prerequisites
- Current SDK version identified
- Changelog reviewed
- Test environment available

## Instructions
1. Assess current configuration
2. Step 2: Review Breaking Changes
3. Step 3: Create Migration Script
4. Step 4: Staged Rollout
5. Step 5: Validation Testing

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [SDK Changelog](https://github.com/juicebox-ai/sdk-js/releases)
- [Migration Guides](https://juicebox.ai/docs/migration)

## Next Steps
After upgrade, verify with `juicebox-prod-checklist` for production readiness.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [migration implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with migration |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox upgrade migration for production environments with multiple constraints and team-specific requirements.