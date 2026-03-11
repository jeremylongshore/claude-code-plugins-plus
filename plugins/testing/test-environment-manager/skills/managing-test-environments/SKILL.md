---
name: managing-test-environments
description: |
  Test provision and manage isolated test environments with configuration and data.
  Use when performing specialized testing.
  Trigger with phrases like "manage test environment", "provision test env", or "setup test infrastructure".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:env-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Test Environment Manager

## Overview

Provision, configure, and manage isolated test environments for reliable test execution. Supports Docker Compose environments, Testcontainers, local service stacks, and ephemeral CI environments. Handles database seeding, service discovery, port allocation, and teardown to ensure each test run operates against a clean, reproducible state.

## Prerequisites

- Docker and Docker Compose installed (for containerized environments)
- Testcontainers library installed if using programmatic container management
- Database client tools (psql, mysql, mongosh) for seed data operations
- Environment variable management via `.env` files or secrets manager
- Sufficient disk space and memory for running service containers

## Instructions

1. Read the project's existing configuration files (`docker-compose.yml`, `.env.test`, `jest.config.*`, `pytest.ini`) to understand current environment setup.
2. Inventory all external dependencies the test suite requires (databases, message queues, cache servers, third-party API stubs).
3. Create or update a `docker-compose.test.yml` defining isolated service containers:
   - Assign non-conflicting ports to avoid collisions with development services.
   - Configure health checks for each service to prevent tests from starting before services are ready.
   - Set resource limits (memory, CPU) to match CI runner constraints.
4. Write seed data scripts that populate databases with baseline test data:
   - Use idempotent migrations that can run repeatedly without error.
   - Create separate seed datasets for unit, integration, and E2E test tiers.
   - Include cleanup scripts that truncate tables without dropping schemas.
5. Generate environment configuration files (`.env.test`) with connection strings, API keys, and feature flags appropriate for testing.
6. Create a startup script that orchestrates the full environment lifecycle:
   - Start containers and wait for health checks to pass.
   - Run database migrations and seed data.
   - Export environment variables for the test runner.
   - Execute the test suite.
   - Tear down containers and clean up volumes.
7. Validate the environment by running a small smoke test suite against the provisioned services.

## Output

- `docker-compose.test.yml` with all required service definitions
- `.env.test` with test-specific configuration values
- Database seed scripts (`seeds/test-data.sql` or equivalent)
- Environment startup/teardown shell script (`scripts/test-env.sh`)
- Health check verification report confirming all services are operational

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Port already in use | Another process or dev environment occupies the port | Use dynamic port allocation or specify alternate ports in `docker-compose.test.yml` |
| Container health check timeout | Service takes too long to initialize | Increase health check `interval` and `retries`; ensure sufficient memory allocation |
| Database seed failure | Migration conflicts or missing schema | Run migrations before seeds; verify migration order; check for schema drift |
| Environment variable not found | `.env.test` not loaded or variable misspelled | Verify dotenv loading order; use `env-cmd` or `dotenv-cli` to inject variables |
| Stale Docker volumes | Previous test data persists across runs | Add `--volumes` flag to `docker-compose down` in teardown; use `tmpfs` mounts |

## Examples

**Docker Compose test environment with PostgreSQL and Redis:**
```yaml
# docker-compose.test.yml
services:
  postgres-test:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: testdb
      POSTGRES_PASSWORD: testpass
    ports: ["5433:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 2s
      retries: 10
  redis-test:
    image: redis:7-alpine
    ports: ["6380:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

**Testcontainers setup in Jest:**
```typescript
import { PostgreSqlContainer } from '@testcontainers/postgresql';

let container;
beforeAll(async () => {
  container = await new PostgreSqlContainer().start();
  process.env.DATABASE_URL = container.getConnectionUri();
}, 30000);
afterAll(async () => { await container.stop(); });
```

## Resources

- Docker Compose documentation: https://docs.docker.com/compose/
- Testcontainers: https://testcontainers.com/
- dotenv-cli for env management: https://github.com/entropitor/dotenv-cli
- 12-Factor App Config: https://12factor.net/config
