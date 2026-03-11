---
name: automating-api-testing
description: |
  Test automate API endpoint testing including request generation, validation, and comprehensive test coverage for REST and GraphQL APIs.
  Use when testing API contracts, validating OpenAPI specifications, or ensuring endpoint reliability.
  Trigger with phrases like "test the API", "generate API tests", or "validate API contracts".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:api-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# API Test Automation

## Overview

Automate comprehensive API endpoint testing for REST and GraphQL APIs including request generation, response validation, schema compliance, authentication flows, and error handling. Supports Supertest (Node.js), REST-assured (Java), httpx/pytest (Python), Postman/Newman collections, and Pact for consumer-driven contract testing. Generates test suites from OpenAPI specifications and GraphQL schemas to ensure complete endpoint coverage.

## Prerequisites

- API testing library installed (Supertest, REST-assured, httpx, or Postman/Newman)
- API specification file (OpenAPI/Swagger YAML/JSON or GraphQL SDL)
- Target API running in a test environment with seeded data
- Authentication credentials or API keys for protected endpoints
- JSON Schema validator (Ajv, jsonschema, or built-in framework assertions)

## Instructions

1. Read the API specification and extract all endpoints:
   - Parse OpenAPI spec to catalog every path, HTTP method, request schema, and response schema.
   - For GraphQL APIs, introspect the schema to list queries, mutations, and subscriptions.
   - Document authentication requirements per endpoint (API key, Bearer token, OAuth, none).
2. Generate test cases for each endpoint:
   - **Success cases**: Send valid requests matching the schema and assert 200/201 responses.
   - **Validation errors**: Send requests with missing required fields, wrong types, and out-of-range values; assert 400 responses.
   - **Authentication**: Test with valid, expired, and missing credentials; assert 200, 401, and 403 respectively.
   - **Not found**: Request non-existent resources; assert 404 responses.
   - **Idempotency**: Send the same PUT/DELETE request twice and verify consistent behavior.
3. Validate response structure against schemas:
   - Assert response Content-Type matches expected (application/json, etc.).
   - Validate response body against the OpenAPI response schema using JSON Schema validation.
   - Check response headers (Cache-Control, Rate-Limit headers, CORS headers).
   - Verify pagination metadata (total count, page number, next/previous links).
4. Test CRUD lifecycle for resource endpoints:
   - Create a resource (POST) and capture the ID.
   - Read it back (GET) and verify all fields match.
   - Update it (PUT/PATCH) and verify changes persisted.
   - Delete it (DELETE) and verify subsequent GET returns 404.
5. Test error handling and edge cases:
   - Send excessively large payloads and verify 413 or graceful rejection.
   - Send requests with unsupported Content-Types and verify 415.
   - Test rate limiting by sending rapid sequential requests.
   - Verify error response format is consistent (standard error schema).
6. For GraphQL APIs, test specifically:
   - Valid queries return expected data shapes.
   - Invalid queries return descriptive error messages.
   - Query depth limiting prevents deeply nested abuse queries.
   - Mutation input validation matches schema constraints.
7. Generate a test coverage report mapping endpoints to test cases.

## Output

- API test files organized by resource in `tests/api/`
- Request/response examples for API documentation
- Schema compliance report for each endpoint
- Endpoint coverage matrix showing tested vs. untested endpoints and methods
- CI pipeline step running API tests against staging environment

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Connection refused | API server not running or wrong base URL | Verify server is up with a health check before test suite starts; check `BASE_URL` config |
| 401 on all requests | Authentication token expired or misconfigured | Refresh token in test setup; verify `Authorization` header format; check token scopes |
| Schema validation fails unexpectedly | API response includes extra fields not in spec | Update OpenAPI spec to include new fields; use `additionalProperties: true` if expected |
| Test data conflicts | Another test modified or deleted the resource | Use unique test data per test; create resources in `beforeEach`; avoid shared fixtures |
| Rate limit hit during test run | Too many requests in quick succession | Add delays between requests or use authenticated sessions with higher limits; run tests serially |

## Examples

**Supertest REST API test suite:**
```typescript
import request from 'supertest';
import { app } from '../src/app';

describe('GET /api/products', () => {
  it('returns a paginated product list', async () => {
    const res = await request(app)
      .get('/api/products?page=1&limit=10')
      .set('Authorization', `Bearer ${token}`)
      .expect(200)
      .expect('Content-Type', /json/);

    expect(res.body.data).toBeInstanceOf(Array);
    expect(res.body.data.length).toBeLessThanOrEqual(10);
    expect(res.body.meta).toMatchObject({ page: 1, limit: 10 });
  });

  it('returns 401 without authentication', async () => {
    await request(app).get('/api/products').expect(401);
  });
});

describe('POST /api/products', () => {
  it('creates a product with valid data', async () => {
    const res = await request(app)
      .post('/api/products')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'Widget', price: 9.99, category: 'tools' })
      .expect(201);

    expect(res.body).toMatchObject({ name: 'Widget', price: 9.99 });
    expect(res.body.id).toBeDefined();
  });

  it('returns 400 for missing required fields', async () => {
    await request(app)
      .post('/api/products')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'Widget' }) // missing price
      .expect(400);
  });
});
```

**GraphQL API test:**
```typescript
it('fetches user by ID', async () => {
  const query = `query { user(id: "1") { id name email } }`;
  const res = await request(app)
    .post('/graphql')
    .send({ query })
    .expect(200);

  expect(res.body.data.user).toMatchObject({ id: '1', name: 'Alice' });
  expect(res.body.errors).toBeUndefined();
});
```

## Resources

- Supertest: https://github.com/ladjs/supertest
- REST-assured (Java): https://rest-assured.io/
- httpx (Python): https://www.python-httpx.org/
- Newman (Postman CLI): https://learning.postman.com/docs/collections/using-newman-cli/
- OpenAPI specification: https://spec.openapis.org/oas/v3.1.0
- Ajv JSON Schema validator: https://ajv.js.org/
