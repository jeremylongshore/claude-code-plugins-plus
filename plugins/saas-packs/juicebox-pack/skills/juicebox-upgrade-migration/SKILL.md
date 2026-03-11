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
- Step 1: Assess Current State
- Step 2: Review Breaking Changes
- Step 3: Create Migration Script
- Step 4: Staged Rollout
- Step 5: Validation Testing

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [SDK Changelog](https://github.com/juicebox-ai/sdk-js/releases)
- [Migration Guides](https://juicebox.ai/docs/migration)

## Next Steps
After upgrade, verify with `juicebox-prod-checklist` for production readiness.
