---
name: langfuse-migration-deep-dive
description: |
  Execute complex Langfuse migrations including data migration and platform changes.
  Use when migrating from other observability platforms, moving between Langfuse instances,
  or performing major infrastructure migrations.
  Trigger with phrases like "langfuse migration", "migrate to langfuse",
  "langfuse data migration", "langfuse platform migration", "switch to langfuse".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive guide for complex migrations to or between Langfuse instances, including cloud-to-self-hosted, LangSmith-to-Langfuse, and zero-downtime dual-write patterns.

## Prerequisites
- Understanding of source and target systems
- Database access (for data migrations)
- Downtime window planned (if needed)
- Rollback plan prepared

## Instructions

### Step 1: Export Data from Source
Paginate through all traces, scores, and datasets. Export to JSON files with rate limiting (200ms between pages).

### Step 2: Set Up Target Instance
For self-hosted: deploy via Docker Compose with PostgreSQL. Configure auth, secrets, and encryption.

### Step 3: Import Data to Target
Recreate traces with original metadata plus `migratedFrom` and `originalId` fields. Flush after each file.

### Step 4: Implement Dual-Write (Zero-Downtime)
During migration, write to both old and new systems. Gradually shift: Week 1 dual-write, Week 3 cutover.

### Step 5: Validate Migration
Compare trace counts (allow 1% variance). Spot-check random traces by `originalId`.

### Step 6: Execute Rollback if Needed
Switch environment variables back to old system and restart.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Exported trace data from source
- Running target Langfuse instance
- Validated data migration
- Dual-write capability for zero-downtime

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Data loss | Incomplete export | Re-run with pagination |
| Duplicate traces | Re-import | Dedupe by originalId |
| Missing metadata | Format mismatch | Update adapter |
| Performance issues | Large import | Use batch processing |

## Examples

### Migration Scenarios
| Scenario | Complexity | Downtime | Data Loss Risk |
|----------|------------|----------|----------------|
| Cloud to Cloud | Low | None | None |
| Self-hosted to Cloud | Medium | Minutes | Low |
| Other platform to Langfuse | High | Hours | Medium |
| SDK version upgrade | Low | None | None |

## Resources
- [Langfuse Self-Hosting](https://langfuse.com/docs/deployment/self-host)
- [Langfuse API Reference](https://langfuse.com/docs/api-reference)
- [Data Migration Best Practices](https://langfuse.com/docs/deployment/migration)