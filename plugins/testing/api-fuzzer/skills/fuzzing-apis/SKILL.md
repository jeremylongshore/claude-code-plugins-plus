---
name: fuzzing-apis
description: |
  Configure perform API fuzzing to discover edge cases, crashes, and security vulnerabilities.
  Use when performing specialized testing.
  Trigger with phrases like "fuzz the API", "run fuzzing tests", or "discover edge cases".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:fuzz-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# API Fuzzer

## Overview

Perform API fuzzing to discover crashes, unhandled exceptions, security vulnerabilities, and edge case failures by sending malformed, unexpected, and boundary-value inputs to API endpoints. Supports RESTler (stateful REST API fuzzing), Schemathesis (OpenAPI-driven property-based testing), custom fuzz harnesses with fast-check, and OWASP ZAP active scanning.

## Prerequisites

- API specification available (OpenAPI/Swagger, GraphQL SDL, or Protobuf definitions)
- Target API running in a test environment (never fuzz production)
- Fuzzing tool installed (Schemathesis, RESTler, or custom harness with fast-check/Hypothesis)
- API authentication credentials for protected endpoints
- Error logging enabled on the target server to capture crashes and stack traces

## Instructions

1. Parse the API specification to identify all endpoints, methods, and input schemas:
   - Read OpenAPI spec files using Glob (`**/openapi.yaml`, `**/swagger.json`).
   - Catalog each endpoint's parameters (path, query, header, body) and their types.
   - Note validation constraints (min/max, pattern, enum, required fields).
2. Configure the fuzzing strategy:
   - **Schema-based**: Generate inputs that violate schema constraints (wrong types, missing fields, extra fields).
   - **Mutation-based**: Start with valid requests and mutate individual fields (bit flips, boundary values, special characters).
   - **Dictionary-based**: Use known problematic inputs (SQL injection, XSS payloads, format strings, null bytes).
3. Define fuzz input categories for each parameter type:
   - **Strings**: Empty, very long (10K+ chars), unicode, null bytes, format strings (`%s%n`), path traversal (`../../etc/passwd`).
   - **Numbers**: 0, -1, MAX_INT, MIN_INT, NaN, Infinity, floats where ints expected.
   - **Arrays**: Empty, single element, thousands of elements, nested arrays, mixed types.
   - **Objects**: Empty, missing required fields, extra unknown fields, deeply nested (100+ levels).
   - **Dates**: Invalid formats, epoch zero, far future, negative timestamps.
4. Execute the fuzzing campaign:
   - Run Schemathesis: `schemathesis run http://localhost:3000/openapi.json --stateful=links`.
   - Or run RESTler: `restler-fuzzer fuzz --grammar_file grammar.py`.
   - Or write custom fuzz tests with fast-check/Hypothesis for targeted endpoints.
   - Set a time budget (30-60 minutes for initial run).
5. Analyze findings:
   - **5xx responses**: Unhandled server errors -- file as bugs.
   - **Crashes/hangs**: Application process terminated or stopped responding.
   - **Resource exhaustion**: Memory/CPU spike from malicious payloads.
   - **Information disclosure**: Stack traces, internal paths, or credentials in error responses.
6. For each finding, create a minimal reproducer (smallest input that triggers the issue).
7. Write regression tests for confirmed bugs to prevent reintroduction.

## Output

- Fuzz campaign report with discovered issues sorted by severity
- Minimal reproducer for each finding (curl command or test case)
- Categorized findings: crashes, unhandled errors, security issues, validation gaps
- Regression test file with one test per confirmed bug
- Coverage metrics showing which endpoints and parameters were fuzzed

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Fuzzer cannot parse API spec | Invalid or incomplete OpenAPI specification | Validate the spec with `swagger-cli validate`; fix schema errors before fuzzing |
| All requests return 401 | Authentication not configured in fuzzer | Provide auth headers via `--set-header "Authorization: Bearer TOKEN"` or config file |
| Server crashes during fuzzing | Unhandled exception or resource exhaustion | Restart the server with a process manager; enable crash dump collection; add OOM killer threshold |
| Too many false positives (500 errors) | Application returns 500 for expected validation errors | Filter known error patterns; configure the fuzzer to ignore specific response bodies |
| Fuzzer generates unrealistic inputs | Schema-based generation produces impossible combinations | Add `x-examples` to the OpenAPI spec; use stateful fuzzing to maintain valid sequences |

## Examples

**Schemathesis OpenAPI fuzzing:**
```bash
# Basic schema-based fuzzing
schemathesis run http://localhost:3000/api/openapi.json \  # 3000: 3 seconds in ms
  --stateful=links \
  --hypothesis-max-examples=500 \  # HTTP 500 Internal Server Error
  --base-url=http://localhost:3000 \  # 3 seconds in ms
  --header "Authorization: Bearer $TEST_TOKEN"

# With specific checks
schemathesis run http://localhost:3000/api/openapi.json \  # 3 seconds in ms
  --checks all \
  --validate-schema=true
```

**fast-check property-based API test:**
```typescript
import fc from 'fast-check';
import request from 'supertest';
import { app } from '../src/app';

test('POST /api/users handles arbitrary input without crashing', async () => {
  await fc.assert(
    fc.asyncProperty(
      fc.record({
        name: fc.string(),
        email: fc.string(),
        age: fc.oneof(fc.integer(), fc.string(), fc.constant(null)),
      }),
      async (body) => {
        const res = await request(app).post('/api/users').send(body);
        expect(res.status).toBeLessThan(500); // No server errors  # HTTP 500 Internal Server Error
      }
    ),
    { numRuns: 200 }  # HTTP 200 OK
  );
});
```

**Custom fuzz dictionary for injection testing:**
```json
[
  "' OR '1'='1",
  "<script>alert(1)</script>",
  "${7*7}",
  "{{7*7}}",
  "../../../etc/passwd",
  "\u0000",
  "A".repeat(100000)  # 100000 = configured value
]
```

## Resources

- Schemathesis: https://schemathesis.readthedocs.io/
- RESTler (Microsoft): https://github.com/microsoft/restler-fuzzer
- fast-check (property-based testing): https://fast-check.dev/
- Hypothesis (Python): https://hypothesis.readthedocs.io/
- OWASP Fuzzing: https://owasp.org/www-community/Fuzzing