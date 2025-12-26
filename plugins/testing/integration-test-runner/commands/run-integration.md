---
name: run-integration
description: Run integration test suites with proper setup and teardown
shortcut: rit
---
# Integration Test Runner

Run integration tests with comprehensive environment setup, database seeding, service orchestration, and cleanup.

## Purpose

Execute integration tests that verify interactions between multiple system components:
- API endpoints with database operations
- Microservices communication
- Third-party service integrations
- Full request/response workflows
- Database transactions and state changes

## Pre-Test Setup

Before running integration tests, ensure:

1. **Environment Configuration**
   - Check for test environment variables
   - Verify test database connections
   - Confirm test API keys/credentials
   - Validate service dependencies are available

2. **Database Preparation**
   - Create/reset test database
   - Run migrations
   - Seed test data
   - Clear any existing test data

3. **Service Dependencies**
   - Start required services (Redis, message queues, etc.)
   - Check service health endpoints
   - Initialize mock services if needed
   - Set up test containers (Docker/Testcontainers)

4. **State Management**
   - Clear caches
   - Reset file system test directories
   - Initialize test state

## Test Execution

Run integration tests with:

```bash
# Run all integration tests
/run-integration

# Run specific test suite
/run-integration api

# Run with specific environment
/run-integration --env staging

# Run with coverage
/run-integration --coverage
```

## Execution Process

1. **Pre-flight checks**
   - Validate environment configuration
   - Check database connectivity
   - Verify service availability
   - Confirm no conflicting processes

2. **Setup phase**
   - Initialize test database
   - Seed required data
   - Start dependent services
   - Configure test environment

3. **Run tests**
   - Execute test suites in order
   - Capture detailed logs
   - Report progress
   - Handle test failures gracefully

4. **Teardown phase**
   - Clean up test data
   - Stop test services
   - Reset environment
   - Generate test reports

## Test Organization

Structure integration tests by:
- **API routes** - Endpoint-specific tests
- **User workflows** - End-to-end user journeys
- **Service interactions** - Cross-service communication
- **Data flows** - Multi-step data processing

## Reporting

Generate comprehensive reports with:
- Test results (pass/fail counts)
- Execution time per test
- Failed test details with stack traces
- Code coverage (if enabled)
- Service logs for failures
- Database state at failure points

## Cleanup

After tests complete:
- Drop test database or truncate tables
- Stop test containers/services
- Remove temporary files
- Clear test caches
- Reset environment variables

## Best Practices Applied

- **Isolation** - Tests don't depend on each other
- **Idempotency** - Tests can run multiple times safely
- **Fast feedback** - Fail fast on setup errors
- **Clear reporting** - Easy to identify failures
- **Proper cleanup** - No test pollution
- **Realistic data** - Test data resembles production

## Example Output

```
Integration Test Runner
=======================

Setup Phase:
 Database connection verified
 Test database created and migrated
 Test data seeded (50 users, 200 products)
 Redis cache cleared
 Services healthy: api, worker, notifications

Running Tests:
 API Authentication Tests (5/5 passed) - 2.3s
 User Management Tests (12/12 passed) - 5.1s
 Order Processing Tests (8/8 passed) - 8.7s
 Payment Integration Tests (3/4 passed) - 4.2s
  └─ test_refund_webhook_handling FAILED
 Notification Tests (6/6 passed) - 3.1s

Results: 34/35 tests passed (97.1%)
Total time: 23.4s
Coverage: 78.3%

Teardown Phase:
 Test database dropped
 Services stopped
 Temp files removed

Report saved to: test-results/integration-2025-10-11-14-30.json
```

## Troubleshooting

Common issues:
- **Connection refused** - Check service is running
- **Database errors** - Verify migrations are current
- **Timeout errors** - Increase test timeouts
- **Port conflicts** - Ensure test ports are available
- **Permission errors** - Check file/database permissions
