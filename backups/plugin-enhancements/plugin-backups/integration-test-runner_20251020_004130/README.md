# Integration Test Runner Plugin

Run and manage integration test suites with automatic environment setup, database seeding, service orchestration, and cleanup.

## Features

- **Automated setup** - Database creation, migrations, seeding
- **Service orchestration** - Start/stop dependent services
- **Environment management** - Test-specific configurations
- **Comprehensive reporting** - Detailed results and logs
- **Proper cleanup** - No test pollution or leftover state
- **Fast feedback** - Fail fast on setup errors

## Installation

```bash
/plugin install integration-test-runner@claude-code-plugins-plus
```

## Usage

### Run all integration tests

```bash
/run-integration
```

### Run specific test suite

```bash
/run-integration api
/run-integration --suite user-workflows
```

### Run with coverage

```bash
/run-integration --coverage
```

### Use shortcut

```bash
/rit
```

## What It Does

### 1. Pre-Test Setup

- Validates environment configuration
- Checks database connectivity
- Verifies service availability
- Confirms no port conflicts

### 2. Environment Preparation

- Creates/resets test database
- Runs database migrations
- Seeds test data
- Starts dependent services (Redis, queues, etc.)
- Initializes test containers

### 3. Test Execution

- Runs test suites in logical order
- Captures detailed execution logs
- Reports progress in real-time
- Handles failures gracefully
- Collects code coverage (if enabled)

### 4. Post-Test Cleanup

- Drops test database or truncates tables
- Stops test services and containers
- Removes temporary files
- Clears test caches
- Resets environment

### 5. Report Generation

- Pass/fail counts
- Execution times
- Failed test details with stack traces
- Code coverage metrics
- Service logs for debugging

## Test Types Supported

- **API Integration** - REST/GraphQL endpoint testing
- **Database Operations** - CRUD operations, transactions
- **Service Communication** - Microservice interactions
- **External APIs** - Third-party integrations (mocked or sandboxed)
- **Message Queues** - Pub/sub, task queues
- **File Operations** - Upload/download workflows
- **Authentication** - Login, tokens, sessions

## Example Workflow

```bash
# 1. Plugin runs pre-flight checks
Checking environment... 
Database available... 
Required services... 

# 2. Sets up test environment
Creating test database... 
Running migrations... 
Seeding test data... 
Starting Redis... 

# 3. Executes test suites
Running API tests... 12/12 passed
Running workflow tests... 8/8 passed
Running integration tests... 15/16 passed (1 failure)

# 4. Generates report
Results: 35/36 passed (97.2%)
Coverage: 81.5%
Time: 42.3s

# 5. Cleans up
Dropping test database... 
Stopping services... 
Cleanup complete... 
```

## Configuration

The plugin looks for test configuration in:

- `test/integration/config.json`
- `.env.test`
- `docker-compose.test.yml`
- Project-specific test configs

Example configuration:

```json
{
  "database": {
    "name": "myapp_test",
    "reset": true,
    "seed": "test/fixtures/seed.sql"
  },
  "services": {
    "redis": "redis://localhost:6380",
    "queue": "amqp://localhost:5673"
  },
  "env": {
    "NODE_ENV": "test",
    "LOG_LEVEL": "error"
  }
}
```

## Best Practices

The plugin enforces integration testing best practices:

- **Test isolation** - No shared state between tests
- **Idempotency** - Can run multiple times safely
- **Realistic data** - Test data resembles production
- **Proper cleanup** - Leaves no trace
- **Clear reporting** - Easy failure diagnosis
- **Fast execution** - Optimized for speed

## Requirements

- Claude Code CLI
- Testing framework (Jest, pytest, RSpec, etc.)
- Database access (PostgreSQL, MySQL, MongoDB, etc.)
- Docker (optional, for service containers)

## Tips

1. **Keep tests fast** - Use minimal data seeding
2. **Parallelize when possible** - Independent tests can run concurrently
3. **Mock external APIs** - Use sandboxes or mocks for third parties
4. **Use transactions** - Rollback after each test for speed
5. **Tag tests** - Separate slow tests for CI optimization

## Troubleshooting

### Tests fail with "connection refused"

Ensure dependent services are running. Check Docker containers or local services.

### Database errors during setup

Verify migrations are current and database user has proper permissions.

### Timeouts during test execution

Increase test timeout values or optimize slow queries.

### Port conflicts

Change test service ports or stop conflicting processes.

## License

MIT
