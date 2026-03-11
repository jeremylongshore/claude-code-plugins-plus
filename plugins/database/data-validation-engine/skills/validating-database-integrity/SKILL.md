---
name: validating-database-integrity
description: |
  Process use when you need to ensure database integrity through comprehensive data validation.
  This skill validates data types, ranges, formats, referential integrity, and business rules.
  Trigger with phrases like "validate database data", "implement data validation rules",
  "enforce data integrity constraints", or "validate data formats".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Data Validation Engine

## Overview

Implement and enforce data integrity rules at the database level using CHECK constraints, triggers, foreign keys, and custom validation functions across PostgreSQL and MySQL. This skill audits existing data for constraint violations, generates validation rules from business requirements, creates migration scripts to apply constraints safely on tables with existing data, and produces data quality reports identifying orphaned records, format violations, and business rule breaches.

## Prerequisites

- Database credentials with ALTER TABLE and CREATE FUNCTION permissions
- `psql` or `mysql` CLI for executing validation queries
- Current schema documentation or access to `information_schema` for column specifications
- Business rules document describing valid data ranges, formats, and relationships
- Backup of production data before applying new constraints (constraints may reject existing invalid data)

## Instructions

1. Audit existing data quality by running validation queries before adding constraints. Check for NULL values in columns that should be required: `SELECT column_name, COUNT(*) FILTER (WHERE column_name IS NULL) AS null_count, COUNT(*) AS total FROM table_name GROUP BY column_name`.

2. Detect orphaned records (broken referential integrity): `SELECT c.id FROM child_table c LEFT JOIN parent_table p ON c.parent_id = p.id WHERE p.id IS NULL`. Document all orphaned records for cleanup or archival before adding foreign key constraints.

3. Validate data format compliance:
   - Email format: `SELECT email FROM users WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'`
   - Phone format: `SELECT phone FROM contacts WHERE phone !~ '^\+?[1-9]\d{6,14}$'`
   - URL format: `SELECT url FROM links WHERE url !~ '^https?://.+'`
   - Date ranges: `SELECT * FROM events WHERE start_date > end_date`

4. Check numeric range violations: `SELECT * FROM products WHERE price < 0 OR price > 999999.99` and `SELECT * FROM users WHERE age < 0 OR age > 150`. Map each column to its valid range based on business rules.

5. Identify duplicate records that violate intended uniqueness: `SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1`. Determine which duplicate to keep (most recent, most complete) and plan deduplication.

6. Generate CHECK constraints for validated rules:
   - `ALTER TABLE products ADD CONSTRAINT chk_price_positive CHECK (price >= 0)`
   - `ALTER TABLE users ADD CONSTRAINT chk_email_format CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')`
   - `ALTER TABLE events ADD CONSTRAINT chk_date_order CHECK (start_date <= end_date)`
   - `ALTER TABLE orders ADD CONSTRAINT chk_status_valid CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))`

7. Create foreign key constraints with appropriate cascade behavior:
   - `ALTER TABLE orders ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT`
   - Use `ON DELETE CASCADE` for dependent data (order_items when order is deleted)
   - Use `ON DELETE SET NULL` for optional relationships (assigned_to when user is deactivated)

8. Implement complex business rule validation using database triggers when CHECK constraints are insufficient:
   - Trigger that prevents order total from exceeding customer credit limit
   - Trigger that enforces at least one admin user per organization
   - Trigger that validates JSON schema for JSONB columns

9. Apply constraints in a safe two-phase approach:
   - Phase 1: Run validation queries to find all violations. Generate data cleanup scripts. Execute cleanup.
   - Phase 2: Apply constraints with `NOT VALID` option (PostgreSQL): `ALTER TABLE users ADD CONSTRAINT chk_email CHECK (email ~ '...') NOT VALID` then `ALTER TABLE users VALIDATE CONSTRAINT chk_email` (validates existing data without blocking writes).

10. Generate a data quality report summarizing: total records per table, violation counts by constraint type, cleanup actions taken, constraints applied, and remaining data quality issues requiring manual review.

## Output

- **Data quality audit report** with violation counts, examples, and severity ratings
- **Data cleanup scripts** (SQL) to fix violations before constraint application
- **Constraint DDL scripts** with CHECK, FOREIGN KEY, NOT NULL, and UNIQUE constraints
- **Validation triggers** for complex business rules beyond simple constraints
- **Ongoing validation queries** for periodic data quality monitoring

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `check constraint violated by existing row` | Existing data fails the new constraint | Run the validation query first to find violations; clean up data; use `NOT VALID` option to add constraint without checking existing data, then validate separately |
| `cannot add foreign key: referenced row not found` | Orphaned child records reference non-existent parent | Clean up orphaned records first with DELETE or UPDATE to valid parent; or insert missing parent records |
| `column cannot be made NOT NULL: contains NULL values` | Existing rows have NULL in the target column | Backfill NULLs with `UPDATE table SET column = default_value WHERE column IS NULL` before adding NOT NULL |
| Trigger function causes performance regression | Complex validation logic executes on every INSERT/UPDATE | Optimize trigger function; use WHEN clause to limit trigger firing; consider CHECK constraints instead of triggers for simple rules |
| Circular foreign key prevents constraint creation | Tables reference each other, preventing creation order | Use `ALTER TABLE ADD CONSTRAINT` after both tables exist; or use `DEFERRABLE INITIALLY DEFERRED` constraints |

## Examples

**Auditing a legacy database with 50,000 invalid email addresses**: Validation query reveals 50,000 of 2M user records have invalid email formats (missing @, double dots, spaces). A cleanup script normalizes common issues (trim whitespace, lowercase) and flags 3,000 unfixable records for manual review. After cleanup, a CHECK constraint with regex validation is applied.

**Enforcing referential integrity on a database without foreign keys**: An application relied on application-level FK enforcement, resulting in 12,000 orphaned order_items, 800 orphaned payments, and 200 orphaned reviews. Cleanup scripts archive orphaned records to backup tables, then foreign key constraints with `ON DELETE CASCADE` are added. A nightly validation job monitors for new orphans.

**Implementing business rules for a financial application**: Constraints enforce: account balance cannot be negative (`CHECK (balance >= 0)`), transfer amount must be positive (`CHECK (amount > 0)`), transaction date cannot be in the future (`CHECK (transaction_date <= CURRENT_DATE)`), and a trigger prevents transfers between accounts owned by different customers unless explicitly authorized.

## Resources

- PostgreSQL CHECK constraints: https://www.postgresql.org/docs/current/ddl-constraints.html
- PostgreSQL triggers: https://www.postgresql.org/docs/current/triggers.html
- MySQL CHECK constraints (8.0.16+): https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html
- Data validation patterns: https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-CHECK-CONSTRAINTS
- NOT VALID constraint option: https://www.postgresql.org/docs/current/sql-altertable.html
