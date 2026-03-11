---
name: vercel-migration-deep-dive
description: |
  Execute Vercel major re-architecture and migration strategies with strangler fig pattern.
  Use when migrating to or from Vercel, performing major version upgrades,
  or re-platforming existing integrations to Vercel.
  Trigger with phrases like "migrate vercel", "vercel migration",
  "switch to vercel", "vercel replatform", "vercel upgrade major".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vercel Migration Deep Dive

## Prerequisites
- Current system documentation
- Vercel SDK installed
- Feature flag infrastructure
- Rollback strategy tested

## Instructions

### Assess current configuration
Document existing implementation and data inventory.

### Step 2: Build Adapter Layer
Create abstraction layer for gradual migration.

### Step 3: Migrate Data
Run batch data migration with error handling.

### Step 4: Shift Traffic
Gradually route traffic to new Vercel integration.

## Output
- Migration assessment complete
- Adapter layer implemented
- Data migrated successfully
- Traffic fully shifted to Vercel

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Vercel Migration Guide](https://vercel.com/docs/migration)

## Overview

Execute Vercel major re-architecture and migration strategies with strangler fig pattern.