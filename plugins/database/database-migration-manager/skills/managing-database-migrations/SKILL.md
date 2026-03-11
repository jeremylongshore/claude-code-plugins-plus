---
name: managing-database-migrations
description: |
  Process use when you need to work with database migrations.
  This skill provides schema migration management with comprehensive guidance and automation.
  Trigger with phrases like "create migration", "run migrations",
  or "manage schema versions".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Migration Manager

## Overview

Create, validate, and execute database schema migrations with full rollback support across PostgreSQL, MySQL, and MongoDB.

## Prerequisites

- Database credentials with DDL permissions (CREATE, ALTER, DROP TABLE)
- Migration framework installed and configured (Flyway, Alembic, Prisma, Knex, or raw SQL versioning)
- Version control for migration files (Git repository)
- Access to a staging database matching production schema for testing migrations
- `psql` or `mysql` CLI for executing and verifying migrations
- Current schema baseline documented or captured via `pg_dump --schema-only`

## Instructions

1. Capture the current schema state before making changes. Run `pg_dump --schema-only -f schema_before.sql` (PostgreSQL) or `mysqldump --no-data > schema_before.sql` (MySQL) to create a reference point.

2. Define the desired schema change clearly: specify table name, column additions/removals/modifications, constraint changes, and index updates. Document whether the change is additive (safe) or destructive (requires data migration).

3. Generate a versioned migration file following the framework's naming convention:
   - Flyway: `V20240115_001__add_status_column_to_orders.sql`
   - Alembic: `alembic revision --autogenerate -m "add status column to orders"`
   - Prisma: Edit `schema.prisma` then `npx prisma migrate dev --name add_status_to_orders`
   - Knex: `npx knex migrate:make add_status_to_orders`

4. Write the UP migration (forward change) with these safety practices:
   - Add new columns as nullable first, then backfill, then set NOT NULL
   - Use `IF NOT EXISTS` for CREATE operations to make migrations idempotent
   - Add explicit transaction wrapping: `BEGIN; ... COMMIT;`
   - Include comments explaining the business reason for each change

5. Write the DOWN migration (rollback) that exactly reverses the UP migration. For column additions, the DOWN drops the column. For table renames, the DOWN renames back. For data transformations, the DOWN must restore original data (store it in a backup column or table if needed).

6. Validate the migration on staging by running the full migration sequence:
   - Apply the UP migration and verify schema matches expectations
   - Run the application test suite against the migrated schema
   - Apply the DOWN migration and verify the schema returns to its original state
   - Re-apply the UP migration to confirm idempotency

7. For zero-downtime migrations on production, follow the expand-contract pattern:
   - Phase 1 (expand): Add new column/table without removing old ones. Deploy application code that writes to both old and new.
   - Phase 2 (migrate): Backfill new column/table from old data in batches.
   - Phase 3 (contract): Deploy application code that reads only from new. Drop old column/table in a future migration.

8. Handle large table migrations (>10M rows) with online DDL tools: `pg_repack` for PostgreSQL, `pt-online-schema-change` for MySQL, or `gh-ost` for MySQL. These tools create a shadow table, replicate changes, then swap atomically.

9. Update the migration history table and verify the migration version matches expectations. Run `flyway info` or `alembic current` to confirm.

10. Document the migration in a changelog with: migration version, description, tables affected, estimated execution time, rollback procedure, and any required application deployments.

## Output

- **Migration files** (UP and DOWN) in the target framework's format
- **Pre-flight validation script** checking prerequisites before migration execution
- **Data backfill scripts** for non-nullable column additions on existing tables
- **Rollback runbook** with step-by-step instructions for reverting in production
- **Migration changelog entry** documenting the change for team reference

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Migration fails with lock timeout | Long-running queries blocking DDL locks on the target table | Set `lock_timeout = '5s'` to fail fast; retry during low-traffic period; use `pg_repack` for lock-free operations |
| Column cannot be dropped because of dependent views | Views or materialized views reference the column being removed | Drop or recreate dependent views first; use `CASCADE` only after verifying all dependents are acceptable to drop |
| NOT NULL constraint violation during migration | Existing rows have NULL values in a column being made NOT NULL | Add a backfill step: `UPDATE table SET column = default_value WHERE column IS NULL` before adding NOT NULL |
| Migration version conflict | Two developers created migrations with the same version number | Use timestamp-based versioning; resolve by renaming one migration and re-running |
| Rollback fails because data was inserted after UP migration | New data in added columns has no place to go in the old schema | Design rollback to handle new data (backup column, log discarded data); accept that some rollbacks are data-lossy |

## Examples

**Adding a status enum column to an orders table**: Generate a migration that: (1) creates the enum type `CREATE TYPE order_status AS ENUM ('pending', 'shipped', 'delivered')`, (2) adds column `ALTER TABLE orders ADD COLUMN status order_status`, (3) backfills `UPDATE orders SET status = 'delivered' WHERE shipped_at IS NOT NULL`, (4) sets NOT NULL `ALTER TABLE orders ALTER COLUMN status SET NOT NULL`. Rollback drops the column and enum type.

**Splitting a monolith users table into users and profiles**: Expand phase adds `profiles` table and triggers to sync data. Migrate phase copies existing profile data in batches of 10,000 rows. Contract phase drops profile columns from users table after application code is updated.

**Renaming a column without downtime**: Create a migration that adds the new column, adds a trigger to sync writes between old and new columns, backfills existing data, deploys application code using the new column name, then drops the old column and trigger in a follow-up migration.

## Resources

- Flyway documentation: https://documentation.red-gate.com/fd
- Alembic tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Prisma Migrate: https://www.prisma.io/docs/orm/prisma-migrate
- pg_repack (lock-free table rewrite): https://reorg.github.io/pg_repack/
- gh-ost (GitHub online schema change): https://github.com/github/gh-ost