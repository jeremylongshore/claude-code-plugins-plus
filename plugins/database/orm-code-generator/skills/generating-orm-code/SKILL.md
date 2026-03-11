---
name: generating-orm-code
description: |
  Execute use when you need to work with ORM code generation.
  This skill provides ORM model and code generation with comprehensive guidance and automation.
  Trigger with phrases like "generate ORM models", "create entity classes",
  or "scaffold database models".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(psql:*), Bash(mysql:*), Bash(mongosh:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# ORM Code Generator

## Overview

Generate type-safe ORM model classes, migration files, and repository patterns from existing database schemas or domain specifications. Supports Prisma, TypeORM, Sequelize, SQLAlchemy, Django ORM, and Drizzle ORM. This skill introspects live databases to produce model code that matches the actual schema, including relationships, constraints, indexes, and custom types.

## Prerequisites

- Database connection string or credentials for schema introspection
- `psql` or `mysql` CLI for querying `information_schema`
- Target ORM framework already installed in the project (`prisma`, `typeorm`, `sqlalchemy`, etc.)
- Node.js/Python/Go runtime matching the target ORM
- Existing project structure to place generated models in the correct directory

## Instructions

1. Introspect the database schema by querying `information_schema.COLUMNS`, `information_schema.TABLE_CONSTRAINTS`, and `information_schema.KEY_COLUMN_USAGE` to extract all tables, columns, data types, nullable flags, defaults, primary keys, foreign keys, and unique constraints.

2. For PostgreSQL, additionally query `pg_catalog.pg_type` for custom enum types and `pg_catalog.pg_index` for index definitions. For MySQL, query `information_schema.STATISTICS` for index details.

3. Map database column types to ORM field types:
   - `varchar/text` -> `String` / `@Column('text')`
   - `integer/bigint` -> `Int` / `@Column('int')`
   - `boolean` -> `Boolean` / `@Column('boolean')`
   - `timestamp/datetime` -> `DateTime` / `@Column('timestamp')`
   - `jsonb/json` -> `Json` / `@Column('jsonb')`
   - `uuid` -> `String` with `@default(uuid())` or `uuid.uuid4`
   - Custom enums -> Generate enum type definitions

4. Generate model classes with proper decorators/attributes:
   - For **Prisma**: Generate `schema.prisma` with `model` blocks, `@id`, `@unique`, `@relation`, and `@default` directives.
   - For **TypeORM**: Generate entity classes with `@Entity()`, `@Column()`, `@PrimaryGeneratedColumn()`, `@ManyToOne()`, `@OneToMany()` decorators.
   - For **SQLAlchemy**: Generate model classes extending `Base` with `Column()`, `ForeignKey()`, `relationship()`, and `__tablename__`.
   - For **Drizzle**: Generate table definitions with `pgTable()`, `serial()`, `varchar()`, `timestamp()`, and `relations()`.

5. Generate relationship mappings from foreign key constraints. Detect one-to-one (unique FK), one-to-many, and many-to-many (junction table with two FKs) patterns automatically. Add both sides of each relationship with proper cascade options.

6. Create migration files that capture the current schema state. For Prisma: `npx prisma migrate dev --name init`. For TypeORM: generate migration with `typeorm migration:generate`. For Alembic: `alembic revision --autogenerate`.

7. Generate repository/service layer with common CRUD operations: `findById`, `findAll` with pagination, `create`, `update`, `delete`, and relationship-aware queries (`findWithRelations`).

8. Add validation decorators or constraints matching database CHECK constraints and NOT NULL columns. Use `class-validator` for TypeORM, Pydantic validators for SQLAlchemy, or Zod schemas for Prisma.

9. Generate TypeScript/Python type definitions or interfaces for API layer consumption, ensuring the ORM models and API types stay synchronized.

10. Validate generated models by running a test migration against a temporary database or by comparing the generated schema against the live database schema with a diff tool.

## Output

- **Model/entity files** with full type annotations, decorators, and relationship mappings
- **Migration files** capturing the initial schema state
- **Enum type definitions** for database enum columns
- **Repository/service classes** with typed CRUD operations
- **Validation schemas** (Zod, class-validator, Pydantic) matching database constraints
- **Type definition files** for API layer consumption

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Circular relationship dependency | Two entities reference each other, causing import cycles | Use lazy loading (`() => RelatedEntity`) in TypeORM; use `ForwardRef` in SQLAlchemy; split into separate files with deferred imports |
| Unknown column type mapping | Database uses custom types, extensions, or domain types not in the standard mapping | Add custom type mapping in generator config; use `@Column({ type: 'text' })` as fallback; register custom transformers |
| Migration conflicts with existing data | Generated migration adds NOT NULL columns without defaults | Add default values to new columns; create a two-phase migration (add nullable, backfill, set NOT NULL) |
| Junction table not detected as many-to-many | Junction table has extra columns beyond the two foreign keys | Model as an explicit entity with two ManyToOne relationships instead of an implicit ManyToMany |
| Schema drift between ORM models and database | Manual database changes not reflected in ORM code | Run introspection again; use `prisma db pull` or `sqlacodegen` to regenerate; diff against existing models |

## Examples

**Prisma schema from PostgreSQL e-commerce database**: Introspect 15 tables including users, orders, products, and categories. Generate `schema.prisma` with proper `@relation` directives, enum types for order status, and `@default(autoincrement())` for serial columns. Output includes Zod validation schemas for each model.

**TypeORM entities from MySQL SaaS application**: Generate entity classes for a multi-tenant application with tenant isolation. Each entity includes a `tenantId` column with a custom `@TenantAware` decorator. Repository layer includes tenant-scoped query methods.

**SQLAlchemy models from legacy database with naming conventions**: Introspect a database with inconsistent naming (mix of camelCase and snake_case). Generate models with `__tablename__` preserving original names while using Pythonic property names. Alembic migration captures the full schema.

## Resources

- Prisma introspection: https://www.prisma.io/docs/orm/prisma-schema/introspection
- TypeORM entity documentation: https://typeorm.io/entities
- SQLAlchemy ORM tutorial: https://docs.sqlalchemy.org/en/20/orm/
- Drizzle ORM schema: https://orm.drizzle.team/docs/sql-schema-declaration
- Django inspectdb command: https://docs.djangoproject.com/en/5.0/howto/legacy-databases/
