---
name: designing-database-schemas
description: |
  Process use when you need to work with database schema design.
  This skill provides schema design and migrations with comprehensive guidance and automation.
  Trigger with phrases like "design schema", "create migration",
  or "model database".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Schema Designer

## Overview

Design normalized relational database schemas from business requirements, entity-relationship diagrams, or existing application code. This skill produces PostgreSQL or MySQL DDL with proper data types, constraints, indexes, and relationships following normalization principles (3NF by default) with strategic denormalization where performance requires it. Schemas include audit columns, soft delete support, and multi-tenancy patterns as needed.

## Prerequisites

- Business domain requirements or existing application models/classes to derive schema from
- `psql` or `mysql` CLI for testing schema DDL
- Target database engine and version (determines available data types and features)
- Expected data volumes and query patterns for sizing and index decisions
- Multi-tenancy requirements (shared schema, schema-per-tenant, or database-per-tenant)

## Instructions

1. Identify all entities (nouns) from the business requirements. Each entity becomes a table. List every attribute (property) of each entity and classify as required or optional.

2. Define primary keys for each table. Prefer `BIGSERIAL` (PostgreSQL) or `BIGINT AUTO_INCREMENT` (MySQL) for surrogate keys. Use `UUID` (via `gen_random_uuid()`) for distributed systems or when IDs are exposed in URLs. Natural keys are acceptable when truly immutable and unique (ISO country codes, IATA airport codes).

3. Normalize the schema to Third Normal Form (3NF):
   - **1NF**: Eliminate repeating groups. Each column holds a single atomic value. No arrays in columns (unless using PostgreSQL array types intentionally).
   - **2NF**: Remove partial dependencies. Every non-key column depends on the entire primary key.
   - **3NF**: Remove transitive dependencies. Non-key columns depend only on the primary key, not on other non-key columns. Extract lookup tables for values that change independently.

4. Define relationships between tables:
   - **One-to-many**: Add a foreign key column on the "many" side referencing the "one" side. Example: `orders.customer_id REFERENCES customers(id)`.
   - **Many-to-many**: Create a junction table with two foreign keys. Example: `product_categories(product_id, category_id)` with a composite primary key.
   - **One-to-one**: Add a foreign key with a UNIQUE constraint, or merge into a single table if entities are always accessed together.

5. Choose appropriate data types with precision:
   - Money: `NUMERIC(12,2)` or `INTEGER` storing cents (never `FLOAT`/`DOUBLE`)
   - Timestamps: `TIMESTAMPTZ` (PostgreSQL) with time zone for events; `DATE` for calendar dates
   - Status fields: `VARCHAR(20)` with CHECK constraint, or create an ENUM type
   - Email: `CITEXT` (PostgreSQL) or `VARCHAR(254)` with CHECK constraint for format validation
   - JSON: `JSONB` (PostgreSQL) for flexible schema attributes; avoid for core relational data

6. Add standard columns to every table:
   - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
   - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` (with trigger for auto-update)
   - `deleted_at TIMESTAMPTZ` for soft delete (add partial index `WHERE deleted_at IS NULL`)

7. Define constraints: NOT NULL on required fields, UNIQUE on natural keys and email addresses, CHECK constraints for value validation (`CHECK (price >= 0)`, `CHECK (status IN ('active', 'inactive'))`), and foreign keys with appropriate ON DELETE behavior (CASCADE, SET NULL, or RESTRICT).

8. Design indexes based on expected query patterns:
   - Primary key index is automatic
   - Foreign key columns: always index these for JOIN performance
   - Columns in WHERE clauses with high selectivity: B-tree index
   - Full-text search columns: GIN index on `tsvector`
   - Composite indexes: match the most common multi-column filter patterns, leftmost column first

9. Apply strategic denormalization where 3NF causes unacceptable query complexity:
   - Materialized views for expensive aggregate queries
   - Denormalized counter columns (with trigger-based updates) for counts displayed on every page load
   - JSON columns for flexible metadata that varies by record type

10. Generate the complete DDL script with CREATE TABLE statements in dependency order (referenced tables first), followed by indexes, triggers, and any seed data for lookup tables.

## Output

- **Complete DDL script** with CREATE TABLE, constraints, indexes, and triggers in executable order
- **Entity-relationship description** listing all tables, columns, types, and relationships
- **Index strategy document** explaining which indexes support which query patterns
- **Seed data scripts** for lookup/reference tables (countries, statuses, categories)
- **Migration file** compatible with the project's migration framework

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Circular foreign key dependency | Tables reference each other, preventing creation in any order | Use `ALTER TABLE ADD CONSTRAINT` after both tables are created; or redesign to eliminate the cycle with a junction table |
| Over-normalization causing excessive JOINs | Every lookup value in its own table, queries require 8+ JOINs | Denormalize low-cardinality, rarely-changing lookup values; use ENUM types for status fields instead of separate tables |
| NUMERIC precision overflow | Monetary values exceed `NUMERIC(10,2)` maximum | Increase precision to `NUMERIC(15,2)` or `NUMERIC(19,4)` for currencies requiring sub-cent precision |
| Schema too rigid for evolving requirements | Frequent ALTER TABLE needed as business rules change | Use JSONB columns for flexible attributes; implement the EAV (Entity-Attribute-Value) pattern for truly dynamic schemas; plan for schema evolution from the start |
| Missing index on foreign key column | JOINs on foreign key columns cause sequential scans | Always create indexes on foreign key columns; PostgreSQL does not auto-index foreign keys (unlike MySQL InnoDB) |

## Examples

**E-commerce schema design**: Tables: `customers`, `addresses` (one-to-many from customers), `products`, `categories` (many-to-many via `product_categories`), `orders`, `order_items` (one-to-many from orders), `payments`. Money stored as `NUMERIC(12,2)`. Soft delete on customers and products. GIN index on `products.search_vector` for full-text search. Composite index `(customer_id, created_at DESC)` on orders for order history pages.

**Multi-tenant SaaS schema with row-level security**: Every table includes `tenant_id BIGINT NOT NULL` with a foreign key to `tenants`. Row-level security policies enforce tenant isolation: `CREATE POLICY tenant_isolation ON orders USING (tenant_id = current_setting('app.tenant_id')::bigint)`. Composite indexes start with `tenant_id` for partition-like query performance.

**Event sourcing schema**: An `events` table with `(aggregate_id, sequence_number)` as composite primary key, `event_type VARCHAR(100)`, `payload JSONB`, `created_at TIMESTAMPTZ`. A `snapshots` table stores materialized state at periodic intervals. Append-only design with no UPDATE or DELETE operations.

## Resources

- PostgreSQL data types: https://www.postgresql.org/docs/current/datatype.html
- Database normalization: https://en.wikipedia.org/wiki/Database_normalization
- PostgreSQL row-level security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Index design guide: https://use-the-index-luke.com/
- Schema design patterns: https://www.postgresql.org/docs/current/ddl.html
