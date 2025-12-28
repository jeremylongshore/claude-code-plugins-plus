---
name: firestore-operations-manager
description: |
  Manage Firebase/Firestore operations including CRUD, queries, batch processing, and index/rule guidance.
  Use when you need to create/update/query Firestore documents, run batch writes, troubleshoot missing indexes, or plan migrations.
  Trigger with phrases like "firestore operations", "create firestore document", "batch write", "missing index", or "fix firestore query".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Firestore Operations Manager

Operate Firestore safely in production: schema-aware CRUD, query/index tuning, batch processing, and guardrails for permissions and cost.

## Overview

Use this skill to design Firestore data access patterns and implement changes with the right indexes, security rules, and operational checks (emulator tests, monitoring, and rollback plans).

## Prerequisites

- A Firebase project with Firestore enabled (or a local emulator setup)
- A clear collection/document schema (or permission to propose one)
- Credentials for the target environment (service account / ADC) and a plan for secrets

## Instructions

1. Identify the operation: create/update/delete/query/batch/migration.
2. Confirm schema expectations and security rules constraints.
3. Implement the change (or propose a patch) using safe patterns:
   - prefer batched writes/transactions where consistency matters
   - add pagination for large queries
4. Check indexes:
   - detect required composite indexes and provide `firestore.indexes.json` updates
5. Validate:
   - run emulator tests or a minimal smoke query
   - confirm cost/perf implications for the query pattern

## Output

- Code changes or snippets for the requested Firestore operation
- Index recommendations (and config updates when needed)
- A validation checklist (emulator commands and production smoke tests)

## Error Handling

- Permission denied: identify the rule/role blocking the operation and propose least-privilege changes.
- Missing index: provide the exact composite index needed for the query.
- Hotspot/latency issues: propose sharding, pagination, or query redesign.

## Examples

**Example: Fix a failing query**
- Request: “This query needs a composite index—what do I add?”
- Result: the exact index definition and a safer query pattern if needed.

**Example: Batch migration**
- Request: “Backfill a new field across 100k docs.”
- Result: batched write strategy, checkpoints, and rollback guidance.

## Resources

- Full detailed guide (kept for reference): `{baseDir}/references/SKILL.full.md`
- Firestore docs: https://firebase.google.com/docs/firestore
- Firestore indexes: https://firebase.google.com/docs/firestore/query-data/indexing
