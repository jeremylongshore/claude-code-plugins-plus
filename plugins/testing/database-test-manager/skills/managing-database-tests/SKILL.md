---
name: managing-database-tests
description: |
  Test database testing including fixtures, transactions, and rollback management.
  Use when performing specialized testing.
  Trigger with phrases like "test the database", "run database tests", or "validate data integrity".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:db-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Test Manager

## Overview

Manage database testing including fixture loading, transaction-based test isolation, migration validation, query performance testing, and data integrity checks. Supports PostgreSQL, MySQL, MongoDB, SQLite (in-memory), and Redis with ORM-agnostic patterns for Prisma, TypeORM, SQLAlchemy, Knex, and Drizzle. Ensures each test runs against a clean database state using transactions with rollback or truncation strategies.

## Prerequisites

- Database instance available for testing (Docker container, in-memory SQLite, or dedicated test server)
- Database client library and ORM installed (Prisma, TypeORM, Knex, SQLAlchemy, etc.)
- Migration files up to date and tested independently
- Test database connection string configured in environment (distinct from development/production)
- Database seed data scripts for baseline test state

## Instructions

1. Set up the test database infrastructure:
   - Use Docker to spin up a dedicated test database: `docker run -d -p 5433:5432 --name test-db postgres:16-alpine`.
   - Or use SQLite in-memory mode for fast unit tests: `sqlite::memory:`.
   - Or use Testcontainers for ephemeral database per test suite.
   - Verify the test database is isolated from development data.
2. Run database migrations against the test database:
   - Execute `npx prisma migrate deploy` or `npx knex migrate:latest --env test`.
   - Verify all migrations apply cleanly to an empty database.
   - Test rollback: run `migrate:rollback` and verify schema reverts correctly.
3. Implement test isolation strategy (choose one):
   - **Transaction rollback**: Wrap each test in a transaction; roll back after assertions. Fastest option.
   - **Truncation**: Truncate all tables in `beforeEach`. Simpler but slower.
   - **Database recreation**: Drop and recreate the database before each test suite. Slowest, most thorough.
4. Create database fixture utilities:
   - Factory functions that insert records and return the created entity with its database-generated ID.
   - Seed functions for standard test scenarios (empty state, populated state, edge cases).
   - Cleanup utilities that handle foreign key ordering for truncation.
5. Write database-specific test cases:
   - **CRUD operations**: Insert, query, update, delete records and verify database state.
   - **Constraint validation**: Attempt invalid inserts (null on NOT NULL, duplicate on UNIQUE) and verify rejection.
   - **Referential integrity**: Verify cascading deletes, foreign key enforcement, and orphan prevention.
   - **Index performance**: Verify queries use expected indexes with EXPLAIN ANALYZE.
   - **Transaction isolation**: Test concurrent updates and verify conflict handling.
6. Test database query performance:
   - Run `EXPLAIN ANALYZE` on critical queries and assert expected index usage.
   - Benchmark query execution time with representative data volumes.
   - Flag queries doing sequential scans on large tables.
7. Validate migration safety:
   - Test each migration can run on a populated database without data loss.
   - Verify backward compatibility (old code works with new schema during rollout).
   - Check migration execution time is acceptable for production deployment.

## Output

- Database test files organized by entity in `tests/database/` or `tests/models/`
- Fixture and factory utility files in `tests/helpers/` or `tests/factories/`
- Migration test scripts validating up/down migrations
- Query performance benchmarks with EXPLAIN ANALYZE output
- Test database Docker Compose configuration

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Foreign key constraint violation during cleanup | Truncation order does not respect foreign key dependencies | Truncate tables in reverse dependency order; or disable FK checks during cleanup (`SET CONSTRAINTS ALL DEFERRED`) |
| Connection pool exhausted | Too many test workers opening separate connections | Use a single shared connection for tests; limit pool size; close connections in `afterAll` |
| Migration fails on test database | Schema drift between development and test databases | Drop and recreate test database; run all migrations from scratch; verify migration checksums |
| Transaction rollback does not clean up | ORM auto-commits or test creates a new connection outside the transaction | Inject the transaction connection into all ORM operations; disable auto-commit in test config |
| Slow test suite due to database I/O | Too many INSERT/DELETE operations per test | Use in-memory SQLite for unit tests; batch seed data; use transaction rollback instead of truncation |

## Examples

**Jest with Prisma transaction rollback:**
```typescript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

describe('UserRepository', () => {
  afterAll(async () => { await prisma.$disconnect(); });

  it('creates and retrieves a user', async () => {
    await prisma.$transaction(async (tx) => {
      const created = await tx.user.create({
        data: { name: 'Alice', email: 'alice@test.com' },
      });
      const found = await tx.user.findUnique({ where: { id: created.id } });
      expect(found).toMatchObject({ name: 'Alice', email: 'alice@test.com' });
      // Transaction rolls back automatically when we throw
      throw new Error('ROLLBACK');
    }).catch((e) => {
      if (e.message !== 'ROLLBACK') throw e;
    });
  });
});
```

**pytest with database fixture and rollback:**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture
def db_session():
    engine = create_engine("postgresql://test:test@localhost:5433/testdb")
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def test_insert_and_query_user(db_session):
    db_session.execute(
        text("INSERT INTO users (name, email) VALUES (:n, :e)"),
        {"n": "Alice", "e": "alice@test.com"}
    )
    result = db_session.execute(text("SELECT name FROM users WHERE email = :e"),
                                 {"e": "alice@test.com"}).fetchone()
    assert result[0] == "Alice"
```

**Migration validation test:**
```typescript
describe('Database Migrations', () => {
  it('applies all migrations to empty database', async () => {
    const result = await exec('npx prisma migrate deploy');
    expect(result.exitCode).toBe(0);
  });

  it('migration is idempotent', async () => {
    await exec('npx prisma migrate deploy');
    const result = await exec('npx prisma migrate deploy');
    expect(result.exitCode).toBe(0); // Second run should succeed (no-op)
  });
});
```

## Resources

- Prisma testing guide: https://www.prisma.io/docs/guides/testing
- SQLAlchemy testing patterns: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
- Testcontainers databases: https://testcontainers.com/modules/databases/
- Knex migrations: https://knexjs.org/guide/migrations.html
- PostgreSQL EXPLAIN ANALYZE: https://www.postgresql.org/docs/current/using-explain.html
