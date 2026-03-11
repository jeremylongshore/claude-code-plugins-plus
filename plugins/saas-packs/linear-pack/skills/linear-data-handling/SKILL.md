---
name: linear-data-handling
description: |
  Data synchronization, backup, and consistency patterns for Linear.
  Use when implementing data sync, creating backups,
  or ensuring data consistency across systems.
  Trigger with phrases like "linear data sync", "backup linear",
  "linear data consistency", "sync linear issues", "linear data export".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement reliable data synchronization, backup, and consistency for Linear integrations using full sync, incremental webhooks, export/backup, consistency checks, and conflict resolution.

## Prerequisites
- Linear API access
- Database for local storage (Drizzle ORM recommended)
- Understanding of eventual consistency

## Instructions

### Step 1: Data Model Mapping
Define Zod schemas for core Linear entities (`LinearIssueSchema`, `LinearProjectSchema`) covering all fields: id, identifier, title, description, priority, estimate, stateId/stateName, teamId/teamKey, assigneeId, projectId, cycleId, timestamps. Use `z.infer` for type exports.

### Step 2: Full Sync Implementation
Build `fullSync()` that paginates through all issues (100 per page), maps each to the local schema (resolving state/team relations), then runs a database transaction to upsert new/updated issues and soft-delete removed ones. Track stats: total, created, updated, deleted, errors.

### Step 3: Incremental Sync with Webhooks
Create `processWebhookSync()` that handles Linear webhook events (create/update/remove) for Issue entities, performing the corresponding database insert, update, or soft-delete with a `syncedAt` timestamp.

### Step 4: Data Export/Backup
Build `createBackup()` that exports teams, projects, cycles, and all issues (with optional comments) via paginated API calls, writing to JSON or CSV format. Include metadata (exportedAt, version).

### Step 5: Data Consistency Checks
Implement `checkConsistency()` that samples remote issues and compares against local state, detecting missing, stale, and orphaned records. Schedule via daily cron; auto-trigger full sync when thresholds are exceeded.

### Step 6: Conflict Resolution
Create `resolveConflict()` supporting four strategies: remote-wins, local-wins, merge (field-level), and manual (throws `ConflictError`). Allow configurable merge fields.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete Zod schemas, full sync with pagination, webhook handler, backup exporter, consistency checker, and conflict resolution code.

## Output
- Zod-validated data model schemas
- Full sync with pagination and transactions
- Incremental webhook sync handler
- Data export/backup utility
- Consistency check with scheduled monitoring
- Configurable conflict resolution

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Sync timeout | Too many records | Use smaller batches |
| Conflict detected | Concurrent edits | Apply conflict resolution strategy |
| Stale data | Missed webhooks | Trigger full sync |
| Export failed | API rate limit | Add delays between requests |

## Examples


**Basic usage**: Apply linear data handling to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear data handling for production environments with multiple constraints and team-specific requirements.

## Resources
- [Linear GraphQL API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- [Data Sync Patterns](https://martinfowler.com/articles/patterns-of-distributed-systems/)
- [Eventual Consistency](https://en.wikipedia.org/wiki/Eventual_consistency)

## Next Steps
Implement enterprise RBAC with `linear-enterprise-rbac`.