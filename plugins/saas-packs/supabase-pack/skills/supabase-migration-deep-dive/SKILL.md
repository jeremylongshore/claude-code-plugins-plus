---
name: supabase-migration-deep-dive
description: |
  Execute Supabase major re-architecture and migration strategies with strangler fig pattern.
  Use when migrating to or from Supabase, performing major version upgrades,
  or re-platforming existing integrations to Supabase.
  Trigger with phrases like "migrate supabase", "supabase migration",
  "switch to supabase", "supabase replatform", "supabase upgrade major".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Supabase Migration Deep Dive

## Prerequisites
- Current system documentation
- Supabase SDK installed
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
Gradually route traffic to new Supabase integration.

## Output
- Migration assessment complete
- Adapter layer implemented
- Data migrated successfully
- Traffic fully shifted to Supabase

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Supabase Migration Guide](https://supabase.com/docs/migration)

## Overview

Execute Supabase major re-architecture and migration strategies with strangler fig pattern.