---
name: comparing-database-schemas
description: |
  Process use when you need to work with schema comparison.
  This skill provides database schema diff and sync with comprehensive guidance and automation.
  Trigger with phrases like "compare schemas", "diff databases",
  or "sync database schemas".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Diff Tool

## Overview

Compare database schemas between two environments (development vs. staging, staging vs.

## Prerequisites

- Connection credentials to both source and target databases
- `psql` or `mysql` CLI configured to connect to both environments
- Read access to `information_schema` and `pg_catalog` (PostgreSQL) or `information_schema` (MySQL)
- Permission to run `pg_dump --schema-only` for full schema extraction
- Understanding of which environment is the "source of truth" (typically the migration-managed environment)

## Instructions

1. Extract the full schema from both databases for comparison:
   - PostgreSQL: `pg_dump --schema-only --no-owner --no-privileges -f schema_source.sql source_db` and repeat for target_db
   - MySQL: `mysqldump --no-data --routines --triggers source_db > schema_source.sql`
   - Alternatively, query `information_schema` directly for programmatic comparison

2. Compare tables present in each database:
   - `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_catalog = 'source_db' EXCEPT SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_catalog = 'target_db'`
   - This reveals tables that exist in source but not in target (and vice versa)

3. Compare columns for each shared table:
   - Query `information_schema.columns` from both databases for: `column_name`, `data_type`, `character_maximum_length`, `is_nullable`, `column_default`, `ordinal_position`
   - Flag differences in data type, nullability, default values, and column ordering
   - Detect added columns (in source, not target) and dropped columns (in target, not source)

4. Compare indexes:
   - PostgreSQL: Query `pg_indexes` for `indexname`, `indexdef` on each database
   - MySQL: Query `information_schema.STATISTICS` for `INDEX_NAME`, `COLUMN_NAME`, `NON_UNIQUE`
   - Flag missing, extra, or differently-defined indexes

5. Compare constraints (primary keys, foreign keys, unique, check):
   - Query `information_schema.table_constraints` and `information_schema.key_column_usage`
   - Detect missing foreign keys, changed constraint names, and altered check constraint expressions

6. Compare functions, stored procedures, and triggers:
   - PostgreSQL: Query `pg_proc` for function signatures and `pg_trigger` for trigger definitions
   - MySQL: Query `information_schema.ROUTINES` and `information_schema.TRIGGERS`
   - Compare function bodies for logical differences

7. Compare enum types and custom types (PostgreSQL):
   - Query `pg_type` and `pg_enum` for enum label differences
   - Detect added or removed enum values (note: PostgreSQL only supports adding enum values, not removing)

8. Generate a structured diff report categorizing differences as:
   - **Added**: Objects in source not present in target (require CREATE statements)
   - **Removed**: Objects in target not present in source (require DROP statements, confirm intentional)
   - **Modified**: Objects differing between source and target (require ALTER statements)

9. Generate migration SQL to synchronize the target database to match the source:
   - CREATE TABLE for new tables, ALTER TABLE ADD COLUMN for new columns
   - ALTER TABLE ALTER COLUMN for type changes, ALTER TABLE DROP COLUMN for removed columns
   - CREATE INDEX / DROP INDEX for index differences
   - Include transaction wrapping and rollback-safe operations

10. Validate the generated migration by applying it to a copy of the target database and re-running the diff. The second diff should report zero differences, confirming the migration produces the expected state.

## Output

- **Schema diff report** listing all differences categorized by type (added, removed, modified)
- **Migration SQL script** to synchronize target schema to match source
- **Rollback SQL script** to reverse the migration if needed
- **Side-by-side comparison** of differing object definitions
- **Drift detection summary** highlighting changes not tracked in migration files

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Connection refused to one database | Network or credential issue on source or target | Verify connection strings; check firewall rules; confirm credentials work with direct `psql` or `mysql` connection |
| Permission denied on `pg_catalog` queries | User lacks read access to system catalogs | Grant `pg_read_all_settings` role; or use `pg_dump --schema-only` which requires fewer privileges |
| False positive differences from default value formatting | PostgreSQL normalizes default expressions differently in different versions | Normalize default value strings before comparison; ignore whitespace differences; compare semantic equivalence |
| Enum type modification blocked | PostgreSQL does not support removing enum values or reordering | Create a new enum type, migrate the column, drop the old type; document this as a multi-step migration |
| Generated migration fails on target | Target has data that violates new constraints | Add data validation queries before constraint creation; backfill default values; handle edge cases in migration |

## Examples

**Detecting schema drift between staging and production**: After 3 months without auditing, the diff reveals: 2 columns added to production manually (not in migrations), 1 index missing from staging, and 3 functions with different implementations. A migration script is generated to bring staging in sync, and the manual production changes are backported into migration files.

**Pre-deployment schema validation**: Before deploying a release with 5 migration files, run the diff between the post-migration staging schema and the expected schema. The diff catches a migration that accidentally dropped a constraint that a later migration depends on. The migration ordering is fixed before production deployment.

**Comparing PostgreSQL schemas across major version upgrade**: Schema extracted from PostgreSQL 14 and compared against PostgreSQL 16 after migration. Diff reveals function signature changes for built-in function calls, updated default values for new parameters, and deprecated syntax in stored procedures. Migration script updates function definitions for the new version.

## Resources

- PostgreSQL information_schema: https://www.postgresql.org/docs/current/information-schema.html
- MySQL information_schema: https://dev.mysql.com/doc/refman/8.0/en/information-schema.html
- pg_dump schema-only mode: https://www.postgresql.org/docs/current/app-pgdump.html
- migra (PostgreSQL schema diff tool): https://github.com/djrobstep/migra
- Skeema (MySQL schema management): https://www.skeema.io/