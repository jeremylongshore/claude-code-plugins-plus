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

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Prerequisites
- Current system documentation
- Vercel SDK installed
- Feature flag infrastructure
- Rollback strategy tested

## Instructions

Migrating to Vercel from another deployment platform or migrating a Vercel-hosted application to a different architecture is most safely done incrementally using the strangler fig pattern. The key risk in any migration is a hard cutover that cannot be quickly reversed if problems emerge. Building gradual traffic shifting into your migration plan gives you the ability to limit user impact during the transition and validate that the new deployment behaves identically to the old one before fully committing.

### Step 1: Assess Current Configuration
Document the existing deployment configuration: build pipeline, environment variables, serverless function patterns, custom headers and redirect rules, domain configuration, and any Vercel-specific features in use (edge functions, incremental static regeneration, middleware). Identify which aspects of the current deployment have no direct equivalent in the target architecture and require architectural decisions before proceeding.

### Step 2: Build Adapter Layer
Create an abstraction layer for gradual migration using Vercel's rewrite rules or middleware to route a percentage of traffic to the new deployment. This allows you to run both versions in parallel and compare behavior under real traffic without fully committing to the migration.

### Step 3: Migrate Data
For migrations involving data store changes alongside the platform migration, run batch data migration with error handling and verification checksums. Keep both data stores in sync during the parallel-run period.

### Step 4: Shift Traffic
Gradually increase traffic to the new deployment, monitoring error rates and latency at each increment before proceeding. Decommission the old deployment only after running fully on the new configuration for a stability period with no regressions.

## Output
- Migration assessment documented with full configuration inventory
- Adapter layer implementing incremental traffic shifting
- Data migrated and verified where applicable
- Traffic fully shifted with old deployment decommissioned after stability period

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Vercel Migration Guide](https://vercel.com/docs/migration)

## Overview

Execute Vercel major re-architecture and migration strategies with strangler fig pattern.