---
name: running-integration-tests
description: |
  Execute integration tests validating component interactions and system integration.
  Use when performing specialized testing.
  Trigger with phrases like "run integration tests", "test integration", or "validate component interactions".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:integration-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Integration Test Runner

## Overview

Execute integration tests that validate interactions between multiple components, services, and external systems. Tests real database queries, API calls between services, message queue publishing/consuming, and file system operations without mocking the integration boundary. Supports Testcontainers for ephemeral service dependencies, Supertest for HTTP integration, and pytest with database fixtures.

## Prerequisites

- Integration test framework installed (Jest + Supertest, pytest, JUnit 5, or Go testing)
- External services running (database, cache, message queue) via Docker Compose or Testcontainers
- Database migrations applied and seed data loaded
- Test configuration with connection strings pointing to test instances (not production)
- Sufficient timeout settings (integration tests are slower than unit tests)

## Instructions

1. Identify integration boundaries to test:
   - API routes with database queries (controller-to-repository flow).
   - Service-to-service HTTP communication.
   - Message queue producers and consumers.
   - File upload/download with storage services.
   - Cache read/write operations (Redis, Memcached).
2. Set up test infrastructure:
   - Start required services using `docker-compose -f docker-compose.test.yml up -d`.
   - Or use Testcontainers to programmatically start/stop containers per test suite.
   - Run database migrations against the test database.
   - Seed baseline data required by the test suite.
3. Write integration tests following these patterns:
   - **API integration**: Send HTTP requests via Supertest and assert responses including headers, status, and body.
   - **Database integration**: Execute the service method and verify database state with direct queries.
   - **Event integration**: Publish a message and verify the consumer processes it correctly.
   - Use real implementations, not mocks, at the integration boundary.
4. Manage test data isolation:
   - Wrap each test in a database transaction and roll back after assertion.
   - Or truncate tables in `beforeEach` and re-seed minimum required data.
   - Use unique identifiers per test to avoid collisions in shared databases.
5. Handle asynchronous operations:
   - Poll for expected state changes with timeout (e.g., wait for queue consumer to process).
   - Use event listeners or callbacks to signal completion.
   - Set generous timeouts (10-30 seconds) for external service interactions.
6. Run integration tests separately from unit tests:
   - Tag with `@integration` or place in a separate directory (`tests/integration/`).
   - Configure CI to run integration tests in a dedicated job with service containers.
7. Generate test results in JUnit XML format for CI reporting.

## Output

- Integration test files in `tests/integration/` organized by feature
- Docker Compose test configuration for service dependencies
- Database seed and teardown scripts
- JUnit XML test results for CI consumption
- Integration test coverage report showing tested integration points

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Connection refused to database | Database container not yet ready | Add `wait-for-it.sh` or health check polling before running tests; increase startup timeout |
| Foreign key constraint violation | Test data inserted in wrong order or cleanup incomplete | Seed data in dependency order; use cascading deletes in teardown; wrap in transactions |
| Flaky test due to race condition | Async consumer has not processed the message yet | Use polling with timeout instead of fixed sleep; add event completion callbacks |
| Test passes locally, fails in CI | CI uses different service versions or network config | Pin Docker image versions; verify environment variables match; check CI service container logs |
| Slow test suite (>5 minutes) | Too many integration tests or insufficient parallelization | Run independent test suites in parallel CI jobs; use Testcontainers reuse mode; limit seed data |

## Examples

**Supertest API integration test:**
```typescript
import request from 'supertest';
import { app } from '../src/app';
import { db } from '../src/database';

describe('POST /api/users', () => {
  beforeEach(async () => { await db.query('DELETE FROM users'); });
  afterAll(async () => { await db.end(); });

  it('creates a user and persists to database', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'Alice', email: 'alice@example.com' })
      .expect(201);

    expect(response.body).toMatchObject({ name: 'Alice' });
    const row = await db.query('SELECT * FROM users WHERE email = $1', ['alice@example.com']);
    expect(row.rows).toHaveLength(1);
  });
});
```

**pytest with database transaction rollback:**
```python
import pytest
from myapp.services import UserService

@pytest.fixture
def db_session(test_database):
    session = test_database.begin_nested()
    yield session
    session.rollback()

def test_create_user_persists_to_db(db_session):
    service = UserService(db_session)
    user = service.create(name="Alice", email="alice@test.com")
    assert user.id is not None
    found = db_session.query(User).filter_by(email="alice@test.com").one()
    assert found.name == "Alice"
```

## Resources

- Supertest: https://github.com/ladjs/supertest
- Testcontainers: https://testcontainers.com/
- pytest database fixtures: https://docs.pytest.org/en/stable/how-to/fixtures.html
- Docker Compose for testing: https://docs.docker.com/compose/use-cases/#testing
- Integration testing strategies: https://martinfowler.com/bliki/IntegrationTest.html
