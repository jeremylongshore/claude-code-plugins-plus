---
name: clickhouse-data-handling
description: |
  Handle data lifecycle in ClickHouse — TTL expiration, data deletion (GDPR),
  column-level encryption, and audit logging with real ClickHouse SQL.
  Use when implementing data retention, fulfilling GDPR/CCPA deletion requests,
  or managing sensitive data in ClickHouse.
  Trigger with "clickhouse data retention", "clickhouse TTL", "clickhouse GDPR",
  "delete data clickhouse", "clickhouse data lifecycle", "clickhouse PII".
allowed-tools: Read, Write, Edit
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Data Handling

## Overview

Manage the full data lifecycle in ClickHouse: TTL-based expiration, GDPR/CCPA
deletion, data masking, partition management, and audit trails. This skill
produces migration SQL and TypeScript client code you write into your project,
then verifies the results against ClickHouse `system.*` tables.

The workflow below is the high-level path — each step links to the full,
copy-ready SQL/TypeScript in [references/implementation.md](references/implementation.md),
with end-to-end scenarios in [references/examples.md](references/examples.md).

## Prerequisites

Before starting, confirm you have:

- Populated ClickHouse tables to operate on (schema comes from the companion
  skill `clickhouse-core-workflow-a`).
- A written data-retention policy: how long each data class is kept, and which
  columns hold PII. The [Data Classification](#data-classification) table maps
  each class to its ClickHouse handling.
- ClickHouse 23.3+ if you plan to use lightweight `DELETE FROM`; older versions
  must use mutation-based `ALTER TABLE ... DELETE`.
- Access to `system.mutations` and `system.parts` to verify deletions.

## Instructions

Work the six steps in order for a new table, or jump to the one you need. Use
`Write`/`Edit` to place the generated SQL into a migration file (or the
TypeScript into your data-access layer), then run it against ClickHouse and
verify via the `system.*` queries. Full code for each step lives in
[references/implementation.md](references/implementation.md).

1. **TTL-based expiration** — attach a `TTL` clause so data self-deletes, or use
   tiered `TO VOLUME` storage (hot → cold → delete) and column-level TTL to null
   out PII while keeping the row. Skeleton:

   ```sql
   ALTER TABLE analytics.events
       MODIFY TTL created_at + INTERVAL 90 DAY;
   ```

2. **GDPR/CCPA deletion** — choose lightweight `DELETE FROM` (23.3+), verifiable
   `ALTER TABLE ... DELETE` (the compliant path), or `DROP PARTITION` for bulk.
   Always confirm completion in `system.mutations`.
3. **Masking & anonymization** — expose a `CREATE VIEW` that `sipHash64`-hashes
   identifiers and shows only email domains, gated by a dictionary allowlist.
4. **DSAR export & delete** — the TypeScript `exportUserData` / `deleteUserData`
   helpers loop every table for one `user_id` and log each deletion.
5. **Audit trail** — an immutable, TTL-free `audit_log` table partitioned by
   month so retention actions are provable.
6. **Retention monitoring** — a `system.tables`/`system.parts` join that reports
   size, age span, and any MergeTree table missing a TTL.

## Data Classification

| Category | Examples | Handling in ClickHouse |
|----------|----------|------------------------|
| PII | Email, name, IP | Column-level TTL, masking views, deletion support |
| Sensitive | API keys, tokens | Never store in ClickHouse — use secret managers |
| Business | Event counts, metrics | Standard TTL, aggregate for long-term retention |
| Audit | Access logs | No TTL, immutable, partitioned by month |

## Output

Applying this skill produces:

- **Migration SQL** — `CREATE TABLE`/`ALTER TABLE` statements adding TTL clauses,
  masking views, and the immutable `audit_log` table, ready to commit as a
  migration file.
- **TypeScript client code** — `exportUserData` and `deleteUserData` functions
  for DSAR and erasure requests against `@clickhouse/client`.
- **Verification queries** — `system.mutations` / `system.parts` / `system.tables`
  SELECTs that prove a deletion finished and flag tables missing retention.
- **An audit record** — one immutable `audit_log` row per compliance action.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Mutation stuck | Large table rewrite | Check `system.mutations`, cancel if needed |
| TTL not expiring | No merges running | `OPTIMIZE TABLE ... FINAL` to force |
| DELETE not working | Old ClickHouse version | Use `ALTER TABLE DELETE` (mutation) |
| Export timeout | Too much user data | Add LIMIT or export in batches |

## Examples

A minimal TTL attach — the smallest useful action:

```sql
ALTER TABLE analytics.events
    MODIFY TTL created_at + INTERVAL 90 DAY;
OPTIMIZE TABLE analytics.events FINAL;   -- force the cleanup now
```

Full worked scenarios — a complete GDPR erasure (export → verifiable delete →
audit log), standing up a retention-safe table with tiered storage, and auditing
for tables missing a retention policy — are in
[references/examples.md](references/examples.md). The step-by-step SQL and
TypeScript each example composes lives in
[references/implementation.md](references/implementation.md).

## Resources

- [TTL for Data Management](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree#table_engine-mergetree-ttl)
- [DELETE Statement](https://clickhouse.com/docs/sql-reference/statements/delete)
- [Mutations](https://clickhouse.com/docs/guides/developer/mutations)
- [references/implementation.md](references/implementation.md) — full SQL + TypeScript for all six steps
- [references/examples.md](references/examples.md) — end-to-end GDPR / retention scenarios

## Next Steps

For role-based access control that restricts who can run these deletion and
export operations, see the companion skill `clickhouse-enterprise-rbac`. For the
table schemas these lifecycle rules attach to, see `clickhouse-core-workflow-a`.
