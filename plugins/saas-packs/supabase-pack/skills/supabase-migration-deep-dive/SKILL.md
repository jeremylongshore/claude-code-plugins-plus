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

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Prerequisites
- Current system documentation
- Supabase SDK installed
- Feature flag infrastructure
- Rollback strategy tested

## Instructions

Large-scale migrations to Supabase are most safely executed using the strangler fig pattern — running the old and new systems in parallel, incrementally routing traffic to Supabase, and only decommissioning the legacy system once confidence is high. Attempting a big-bang cutover introduces significant rollback complexity, especially if data has already been modified on the new system. Plan your rollback checkpoint before starting any traffic shift.

### Step 1: Assess Current Configuration
Document existing implementation and data inventory. Catalog all tables, indexes, stored procedures, and integration points that must be replicated in Supabase. Identify data that requires transformation or normalization during migration, and flag any features in the legacy system that have no direct equivalent in Supabase.

### Step 2: Build Adapter Layer
Create an abstraction layer that routes requests to either the legacy system or Supabase based on a feature flag. This allows you to test real traffic against Supabase for a subset of users before committing to the migration, and it provides an instant rollback path by flipping the flag back.

### Step 3: Migrate Data
Run batch data migration with error handling. Migrate in chunks, verify row counts and checksums after each batch, and maintain a migration log that records which records have been moved. Keep the legacy and Supabase datasets in sync during the parallel-run period using a change data capture approach.

### Step 4: Shift Traffic
Gradually route traffic to the new Supabase integration, increasing the percentage over days rather than hours. Monitor error rates and latency at each increment before proceeding. Decommission the legacy system only after running fully on Supabase for a stability period.

## Output
- Migration assessment documented with full data inventory
- Adapter layer implemented with feature-flag-controlled routing
- Data migrated and verified against checksums
- Traffic fully shifted to Supabase with legacy system decommissioned

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Supabase Migration Guide](https://supabase.com/docs/migration)

## Overview

Execute Supabase major re-architecture and migration strategies with strangler fig pattern.