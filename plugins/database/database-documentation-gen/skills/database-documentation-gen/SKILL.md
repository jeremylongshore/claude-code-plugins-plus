---
name: database-documentation-gen
description: |
  Process use when you need to work with database documentation.
  This skill provides automated documentation generation with comprehensive guidance and automation.
  Trigger with phrases like "generate docs", "document schema",
  or "create database documentation".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Documentation Generator

## Overview

Generate comprehensive database documentation by introspecting live PostgreSQL or MySQL schemas, extracting table structures, column descriptions, relationships, indexes, constraints, stored procedures, and views. Produces human-readable documentation in Markdown format including entity-relationship descriptions, data dictionary, and column-level metadata.

## Prerequisites

- Database credentials with read access to `information_schema`, `pg_catalog` (PostgreSQL), or system tables (MySQL)
- `psql` or `mysql` CLI for executing introspection queries
- Target output directory for generated documentation files
- Existing column comments (`COMMENT ON COLUMN`) enhance output quality significantly
- Knowledge of the business domain for meaningful table/column descriptions

## Instructions

1. Extract the complete table inventory: `SELECT table_name, obj_description((table_schema || '.' || table_name)::regclass) AS table_comment FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name` (PostgreSQL). For MySQL: `SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()`.

2. For each table, extract column details: `SELECT c.column_name, c.data_type, c.character_maximum_length, c.is_nullable, c.column_default, pgd.description AS column_comment FROM information_schema.columns c LEFT JOIN pg_catalog.pg_description pgd ON pgd.objsubid = c.ordinal_position AND pgd.objoid = (c.table_schema || '.' || c.table_name)::regclass WHERE c.table_name = 'target_table' ORDER BY c.ordinal_position`.

3. Extract primary key and unique constraint definitions: `SELECT tc.constraint_name, tc.constraint_type, kcu.column_name FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name WHERE tc.table_name = 'target_table' AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE')`.

4. Extract foreign key relationships to build the relationship map: `SELECT tc.table_name AS child_table, kcu.column_name AS child_column, ccu.table_name AS parent_table, ccu.column_name AS parent_column, rc.delete_rule, rc.update_rule FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name JOIN information_schema.referential_constraints rc ON tc.constraint_name = rc.constraint_name JOIN information_schema.constraint_column_usage ccu ON rc.unique_constraint_name = ccu.constraint_name WHERE tc.constraint_type = 'FOREIGN KEY'`.

5. Extract index definitions: `SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname` (PostgreSQL). For MySQL: `SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, NON_UNIQUE, SEQ_IN_INDEX FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX`.

6. Extract views and their definitions: `SELECT viewname, definition FROM pg_views WHERE schemaname = 'public'`. Document each view with its purpose, source tables, and any filtering logic.

7. Extract functions and stored procedures: `SELECT routine_name, routine_type, data_type AS return_type FROM information_schema.routines WHERE routine_schema = 'public'`. Include function signatures and parameter descriptions.

8. Generate the data dictionary in Markdown format with one section per table containing: table description, column table (name, type, nullable, default, description), primary key, foreign keys with referenced table, indexes, and any check constraints.

9. Generate an entity-relationship summary listing all relationships: `parent_table (parent_column) -> child_table (child_column)` with cardinality (one-to-many, many-to-many via junction tables).

10. Generate table statistics for context: `SELECT relname, n_live_tup AS row_count, pg_size_pretty(pg_total_relation_size(relid)) AS total_size FROM pg_stat_user_tables ORDER BY n_live_tup DESC`. Include approximate row counts and table sizes in the documentation.

## Output

- **Data dictionary** (Markdown) with complete column-level documentation for every table
- **Entity-relationship description** listing all foreign key relationships with cardinality
- **Index catalog** documenting all indexes with their columns and purpose
- **View definitions** with source table references and business logic descriptions
- **Schema statistics** including table sizes, row counts, and index sizes

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Missing column comments | `COMMENT ON COLUMN` not used in the database | Generate inferred descriptions based on column name patterns; flag columns needing manual description |
| Permission denied on pg_catalog | Restricted database user without catalog access | Request `pg_read_all_settings` role; or use `pg_dump --schema-only` as an alternative schema source |
| Large schema with 500+ tables | Documentation generation takes too long or produces unmanageable output | Generate per-schema or per-module documentation; create a table-of-contents index; filter to specific table prefixes |
| Custom types not resolved | PostgreSQL domain types or composite types not in standard introspection | Query `pg_type` for custom type definitions; include type documentation in a separate section |
| Stale documentation after schema change | Documentation not regenerated after migration | Integrate documentation generation into CI/CD pipeline; run after migration step |

## Examples

**Generating documentation for a 50-table e-commerce database**: Introspect all tables in the `public` schema, producing a 200-line Markdown data dictionary. Each table section includes column descriptions derived from `COMMENT ON COLUMN` annotations, foreign key relationship arrows, and index listings. Junction tables are identified and documented as many-to-many relationships.

**Creating onboarding documentation for a new team member**: Generate schema documentation with table sizes and row counts to help new developers understand which tables are central (large, many relationships) and which are auxiliary (small, few references). The relationship map shows the core entity graph: users -> orders -> order_items -> products.

**Audit-ready documentation for compliance**: Generate documentation including all constraints, check rules, and default values for each column. Flag columns containing PII (matching patterns like `email`, `phone`, `ssn`, `address`) and document their data protection controls. Output includes timestamp of generation and database version.

## Resources

- PostgreSQL system catalogs: https://www.postgresql.org/docs/current/catalogs.html
- PostgreSQL information_schema: https://www.postgresql.org/docs/current/information-schema.html
- MySQL information_schema reference: https://dev.mysql.com/doc/refman/8.0/en/information-schema.html
- SchemaSpy (database documentation tool): https://schemaspy.org/
- dbdocs.io (database documentation hosting): https://dbdocs.io/