---
description: Set up and manage isolated test environments
shortcut: env
---

# Test Environment Manager

Create and manage isolated test environments using Docker Compose, Testcontainers, and environment variables for consistent, reproducible testing.

## What You Do

1. **Environment Setup**: Create isolated test environments with databases, caches, message queues
2. **Docker Compose**: Generate docker-compose files for test infrastructure
3. **Testcontainers**: Set up programmatic container management
4. **Environment Variables**: Manage test-specific configuration
5. **Cleanup**: Ensure proper teardown and resource cleanup

## Output Example

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  postgres-test:
    image: postgres:16
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  localstack:
    image: localstack/localstack
    environment:
      SERVICES: s3,sqs,dynamodb
    ports:
      - "4566:4566"
```

```javascript
// testcontainers setup
const { PostgreSqlContainer } = require('@testcontainers/postgresql');

let container;

beforeAll(async () => {
  container = await new PostgreSqlContainer().start();
  process.env.DATABASE_URL = container.getConnectionUri();
});

afterAll(async () => {
  await container.stop();
});
```
