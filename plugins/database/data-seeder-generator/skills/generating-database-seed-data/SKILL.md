---
name: generating-database-seed-data
description: |
  Process this skill enables AI assistant to generate realistic test data and database seed scripts for development and testing environments. it uses faker libraries to create realistic data, maintains relational integrity, and allows configurable data volumes. u... Use when working with databases or data models. Trigger with phrases like 'database', 'query', or 'schema'.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Data Seeder Generator

## Overview

Generate realistic database seed scripts that populate development and testing environments with representative data. This skill creates seed data that respects foreign key relationships, unique constraints, check constraints, and data type validations using Faker libraries (faker.js, Faker for Python, or raw SQL with random functions).

## Prerequisites

- Database schema definition (SQL DDL, ORM models, or Prisma schema) to understand table structures
- Target database connection for schema introspection (optional, can work from DDL files)
- Faker library available: `@faker-js/faker` (Node.js), `faker` (Python), or `Bogus` (.NET)
- Knowledge of referential integrity constraints (foreign keys, cascades)
- Target data volume per table (e.g., 100 users, 1000 orders, 5000 line items)

## Instructions

1. Analyze the database schema to catalog all tables, columns, data types, constraints, and foreign key relationships. Build a dependency graph where parent tables (referenced by foreign keys) must be seeded before child tables.

2. Determine the seeding order by topologically sorting the dependency graph. Tables with no foreign keys are seeded first (users, categories, products), then tables referencing them (orders, reviews), then junction tables and deeply nested tables last.

3. Map each column to an appropriate Faker generator based on column name and data type:
   - `first_name`, `last_name` -> `faker.person.firstName()`, `faker.person.lastName()`
   - `email` -> `faker.internet.email()` with unique enforcement
   - `phone` -> `faker.phone.number()`
   - `address`, `city`, `state`, `zip` -> `faker.location.*`
   - `created_at`, `updated_at` -> `faker.date.between({ from: '2023-01-01', to: '2024-12-31' })`
   - `price`, `amount` -> `faker.commerce.price({ min: 1, max: 999 })`
   - `description`, `bio` -> `faker.lorem.paragraph()`
   - `status` -> Random selection from CHECK constraint values or enum values
   - `uuid` -> `faker.string.uuid()`

4. Generate foreign key values by referencing previously inserted parent records. Store parent IDs in arrays during generation and randomly select from them for child records. Ensure every parent has at least one child (if the relationship is expected) and distribute children realistically (e.g., Zipf distribution where some users have many orders, most have few).

5. Handle unique constraints by tracking generated values in a Set and regenerating on collision. For email addresses, append a counter or use `faker.internet.email({ firstName, lastName })` with unique names.

6. Respect CHECK constraints and ENUM types by reading the allowed values from the schema and restricting random selection to valid options. For range constraints (`CHECK (age >= 18 AND age <= 120)`), configure Faker to generate within the valid range.

7. Generate the seed script in the appropriate format:
   - **Raw SQL**: `INSERT INTO users (name, email, ...) VALUES ('John Doe', 'john@example.com', ...);` with proper escaping
   - **TypeORM/Prisma**: TypeScript seed file using `prisma.user.createMany()` or `repository.save()`
   - **Django**: Python fixtures in JSON format or management command
   - **Knex**: JavaScript seed file using `knex('users').insert([...])`

8. Make seed scripts idempotent: wrap in a transaction, truncate target tables in reverse dependency order before inserting, or use upsert operations (`ON CONFLICT DO NOTHING`).

9. Add configurable volume control: accept a scale factor parameter that multiplies base counts (scale=1: 100 users, scale=10: 1000 users). Maintain consistent ratios between related tables (1 user : 5 orders : 15 line items).

10. Validate the generated seed data by running it against an empty database, then checking: all foreign key references resolve, unique constraints hold, check constraints pass, and row counts match expectations.

## Output

- **Seed script files** in SQL, TypeScript, Python, or JavaScript format
- **Faker configuration** mapping columns to appropriate generators
- **Dependency order** listing the correct table insertion sequence
- **Validation queries** to verify seed data integrity after insertion
- **Volume configuration** with scale factor and per-table row counts

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Foreign key constraint violation during seeding | Child records reference parent IDs that do not exist | Verify seeding order follows dependency graph; ensure parent seed completes before child seed starts |
| Unique constraint violation | Faker generated duplicate values for unique columns | Track generated values in a Set; use `faker.helpers.unique()` wrapper; append sequential suffix for high-volume unique fields |
| CHECK constraint violation | Generated value outside allowed range or not in enum list | Read CHECK constraints from schema; configure Faker min/max ranges; restrict enum selection to valid values |
| Seed script too slow for large volumes | Individual INSERT statements instead of batch operations | Use batch inserts (`INSERT INTO ... VALUES (...), (...), (...)`); use COPY command for PostgreSQL; disable indexes during bulk insert |
| Unrealistic data distribution | All records have uniform random values | Use weighted random selection for status fields; apply Zipf distribution for popularity-based relationships; generate time-series data with realistic patterns |

## Examples

**Seeding an e-commerce database with 10,000 orders**: Generate 500 users, 200 products across 15 categories, 10,000 orders (distributed over 12 months with higher volume in November-December), and 35,000 line items. Each order has 1-5 line items, prices follow a realistic distribution ($5-$500 with most under $50), and order statuses follow a funnel pattern (70% delivered, 15% shipped, 10% processing, 5% cancelled).

**Creating test data for a multi-tenant SaaS application**: Generate 5 tenants, each with 20-100 users, organization settings, and tenant-specific data. Tenant isolation is maintained in seed data by assigning all records to a specific tenant_id. One "demo" tenant has curated showcase data with meaningful names and descriptions.

**Populating a social media prototype**: Generate 1,000 users with profile photos (sample image URLs from picsum.photos), 5,000 posts with timestamps following a realistic posting pattern (more activity on weekdays, peak at noon), 15,000 comments with reply threading (30% of comments are replies to other comments), and 50,000 likes distributed by post popularity.

## Resources

- faker.js documentation: https://fakerjs.dev/
- Python Faker: https://faker.readthedocs.io/
- Prisma seeding guide: https://www.prisma.io/docs/orm/prisma-migrate/workflows/seeding
- Knex seed files: https://knexjs.org/guide/migrations.html#seed-files
- PostgreSQL COPY command: https://www.postgresql.org/docs/current/sql-copy.html