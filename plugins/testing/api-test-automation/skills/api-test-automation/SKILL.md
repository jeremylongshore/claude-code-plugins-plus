---
name: automating-api-testing
description: |
  Automate API endpoint testing including request generation, validation, and comprehensive test coverage for REST and GraphQL APIs.
  Use when testing API contracts, validating OpenAPI specifications, or ensuring endpoint reliability.
  Trigger with phrases like "test the API", "generate API tests", or "validate API contracts".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:api-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure you have:
- API definition files (OpenAPI/Swagger, GraphQL schema, or endpoint documentation)
- Base URL for the API service (development, staging, or test environment)
- Authentication credentials or API keys if endpoints require authorization
- Testing framework installed (Jest, Mocha, Supertest, or equivalent)
- Network connectivity to the target API service

## Instructions

### Step 1: Analyze API Definition
Examine the API structure and endpoints:
1. Use Read tool to load OpenAPI/Swagger specifications from {baseDir}/api-specs/
2. Identify all available endpoints, HTTP methods, and request/response schemas
3. Document authentication requirements and rate limiting constraints
4. Note any deprecated endpoints or breaking changes

### Step 2: Generate Test Cases
Create comprehensive test coverage:
1. Generate CRUD operation tests (Create, Read, Update, Delete)
2. Add authentication flow tests (login, token refresh, logout)
3. Include edge case tests (invalid inputs, boundary conditions, malformed requests)
4. Create contract validation tests against OpenAPI schemas
5. Add performance tests for critical endpoints

### Step 3: Execute Test Suite
Run automated API tests:
1. Use Bash(test:api-*) to execute test framework with generated test files
2. Validate HTTP status codes match expected responses (200, 201, 400, 401, 404, 500)
3. Verify response headers (Content-Type, Cache-Control, CORS headers)
4. Validate response body structure against schemas using JSON Schema validation
5. Test authentication token expiration and renewal flows

### Step 4: Generate Test Report
Document results in {baseDir}/test-reports/api/:
- Test execution summary with pass/fail counts
- Coverage metrics by endpoint and HTTP method
- Failed test details with request/response payloads
- Performance benchmarks (response times, throughput)
- Contract violation details if schema mismatches detected

## Output

The skill generates structured API test artifacts:

### Test Suite Files
Generated test files organized by resource:
- `{baseDir}/tests/api/users.test.js` - User endpoint tests
- `{baseDir}/tests/api/products.test.js` - Product endpoint tests
- `{baseDir}/tests/api/auth.test.js` - Authentication flow tests

### Test Coverage Report
- Endpoint coverage percentage (target: 100% for critical paths)
- HTTP method coverage per endpoint (GET, POST, PUT, PATCH, DELETE)
- Authentication scenario coverage (authenticated vs. unauthenticated)
- Error condition coverage (4xx and 5xx responses)

### Contract Validation Results
- OpenAPI schema compliance status for each endpoint
- Breaking changes detected between specification versions
- Undocumented endpoints or parameters found in implementation
- Response schema violations with diff details

### Performance Metrics
- Average response time per endpoint
- 95th and 99th percentile latencies
- Requests per second throughput measurements
- Timeout occurrences and slow endpoint identification

## Error Handling

Common issues and solutions:

**Connection Refused**
- Error: Cannot connect to API service at specified base URL
- Solution: Verify service is running using Bash(test:api-healthcheck); check network connectivity and firewall rules

**Authentication Failures**
- Error: 401 Unauthorized or 403 Forbidden on protected endpoints
- Solution: Verify API keys are valid and not expired; ensure bearer token format is correct; check scope permissions

**Schema Validation Errors**
- Error: Response does not match OpenAPI schema definition
- Solution: Update OpenAPI specification to match actual API behavior; file bug if API implementation is incorrect

**Timeout Errors**
- Error: Request exceeded configured timeout threshold
- Solution: Increase timeout for slow endpoints; investigate performance issues on API server; add retry logic for transient failures

## Resources

### API Testing Frameworks
- Supertest for Node.js HTTP assertion testing
- REST-assured for Java API testing
- Postman/Newman for collection-based API testing
- Pact for contract testing and consumer-driven contracts

### Validation Libraries
- Ajv for JSON Schema validation
- OpenAPI Schema Validator for spec compliance
- Joi for Node.js schema validation
- GraphQL Schema validation tools

### Best Practices
- Test against non-production environments to avoid data corruption
- Use test data factories to create consistent test fixtures
- Implement proper test isolation with database cleanup between tests
- Version control test suites alongside API specifications
- Run tests in CI/CD pipeline for continuous validation

## Overview


This skill provides automated assistance for api test automation tasks.
This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.