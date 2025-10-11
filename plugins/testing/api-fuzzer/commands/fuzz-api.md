---
description: Fuzz test APIs with malformed inputs and edge cases
shortcut: fuzz
---

# API Fuzzer

Automated fuzz testing for REST APIs to discover vulnerabilities, crashes, and unexpected behavior through malformed inputs, boundary values, and random payloads. This command generates comprehensive fuzz test suites targeting injection attacks, input validation failures, and edge cases.

## Design Decisions

**Why fuzz testing matters:**
- **Security**: Discovers SQL injection, XSS, command injection vulnerabilities
- **Robustness**: Finds crashes from unexpected inputs before users do
- **Edge cases**: Uncovers boundary conditions developers didn't consider
- **Compliance**: Validates input sanitization meets security standards

**Alternatives considered:**
- **Manual testing**: Too slow, can't cover mutation space
- **Property-based testing**: Good for unit tests, less suited for API integration
- **Penetration testing tools**: Expensive, requires security expertise
- **Static analysis**: Misses runtime-only issues

**This approach balances**: Automation, coverage, security focus, and integration with CI/CD.

## When to Use

Use API fuzzing when:
- Testing security-critical APIs (auth, payment, admin endpoints)
- Validating input sanitization and validation logic
- Finding edge cases before production incidents
- Meeting security compliance requirements (PCI-DSS, SOC 2)
- Testing third-party API integration error handling
- Preparing for penetration testing or security audits

Don't use when:
- API has no user input (static data endpoints)
- Building proof-of-concept with no security requirements
- Input validation is already exhaustively tested
- Time-sensitive release without CI/CD integration

## Prerequisites

- Existing REST API with endpoints to test
- Node.js 16+ or Python 3.8+ for fuzzing scripts
- API documentation (OpenAPI/Swagger or manual endpoint list)
- (Optional) Authentication credentials or test accounts
- (Optional) CI/CD pipeline for automated fuzzing
- (Optional) Security monitoring tools (SIEM, IDS)

## Process

1. **Identify Attack Surface**
   - List all API endpoints accepting user input
   - Identify input types (strings, numbers, JSON, files)
   - Prioritize high-risk endpoints (auth, admin, payment)

2. **Generate Fuzz Inputs**
   - Malformed data (null, undefined, empty, overflow)
   - Injection payloads (SQL, XSS, command injection)
   - Boundary values (max int, negative, infinity)
   - Type confusion (string as int, object as array)

3. **Execute Fuzz Tests**
   - Send fuzz inputs to all endpoints
   - Monitor responses for crashes, 500 errors, timeouts
   - Capture stack traces and error details

4. **Analyze Results**
   - Categorize vulnerabilities by severity (critical, high, medium)
   - Create reproducible test cases for failures
   - Generate security report with findings

5. **Remediate and Retest**
   - Fix discovered vulnerabilities
   - Add regression tests for fixed issues
   - Rerun fuzzer to verify fixes

## Output Format

### Jest Fuzz Test Suite (Node.js)

```javascript
// tests/api-fuzzer.test.js
const axios = require('axios');

const API_BASE = process.env.API_URL || 'http://localhost:3000';

// Fuzz input generators
const fuzzInputs = {
  // String mutations
  strings: [
    '', // Empty
    null,
    undefined,
    ' ', // Whitespace
    'A'.repeat(10000), // Very long
    'A'.repeat(1000000), // Extremely long
    '<script>alert(1)</script>', // XSS
    '<img src=x onerror=alert(1)>', // XSS variant
    '${7*7}', // Template injection
    '{{7*7}}', // Template injection variant
    '\x00', // Null byte
    '\n\r\t', // Control characters
    '../../etc/passwd', // Path traversal
    '../../../etc/passwd', // Path traversal variant
    '\\x41\\x42\\x43', // Hex encoding
  ],

  // SQL injection payloads
  sqlInjection: [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "1; DROP TABLE users--",
    "1' UNION SELECT NULL, NULL--",
    "admin'--",
    "' OR 1=1--",
    "1' ORDER BY 10--", // Column enumeration
  ],

  // Number mutations
  numbers: [
    0,
    -1,
    1,
    999999999999999999, // Large positive
    -999999999999999999, // Large negative
    Infinity,
    -Infinity,
    NaN,
    Number.MAX_SAFE_INTEGER,
    Number.MIN_SAFE_INTEGER,
    Number.MAX_VALUE,
    Number.MIN_VALUE,
    3.14159265358979323846, // Floating point
  ],

  // Boolean mutations
  booleans: [
    true,
    false,
    'true',
    'false',
    1,
    0,
    'yes',
    'no',
  ],

  // Object/Array mutations
  structures: [
    {},
    [],
    { __proto__: { polluted: true } }, // Prototype pollution
    { constructor: { prototype: { polluted: true } } },
    [[[[[]]]]]], // Deeply nested
    new Array(10000).fill('x'), // Large array
  ],

  // Special characters
  special: [
    '!@#$%^&*()',
    '"><script>alert(1)</script>',
    '%00', // URL-encoded null byte
    '%0A', // URL-encoded newline
    '\\', // Backslash
    '/', // Forward slash
    '..\\..\\..\\', // Windows path traversal
  ],
};

describe('API Fuzz Testing', () => {
  describe('POST /api/users - Create User', () => {
    it('handles malformed string inputs gracefully', async () => {
      for (const input of fuzzInputs.strings) {
        try {
          const response = await axios.post(`${API_BASE}/api/users`, {
            name: input,
            email: 'test@example.com',
          }, { validateStatus: () => true }); // Accept all status codes

          // Should not crash (500) or hang
          expect(response.status).not.toBe(500);
          expect(response.status).toBeLessThan(500);

          // Should return proper error for invalid input
          if (response.status >= 400) {
            expect(response.data).toHaveProperty('error');
          }
        } catch (error) {
          // Network errors are acceptable (timeouts, connection refused)
          if (error.code !== 'ECONNABORTED' && error.code !== 'ECONNREFUSED') {
            throw error;
          }
        }
      }
    });

    it('prevents SQL injection', async () => {
      for (const payload of fuzzInputs.sqlInjection) {
        const response = await axios.post(`${API_BASE}/api/users`, {
          name: payload,
          email: payload,
        }, { validateStatus: () => true });

        // Should not execute SQL
        expect(response.status).not.toBe(200);
        expect(response.status).toBe(400); // Should be validation error

        // Should not leak database errors
        if (response.data.error) {
          expect(response.data.error.toLowerCase()).not.toMatch(/sql|database|query/);
        }
      }
    });

    it('handles numeric boundary values', async () => {
      for (const input of fuzzInputs.numbers) {
        const response = await axios.post(`${API_BASE}/api/users`, {
          age: input,
          name: 'Test User',
          email: 'test@example.com',
        }, { validateStatus: () => true });

        expect(response.status).not.toBe(500);
        // Should validate range
        if (input < 0 || input > 150) {
          expect(response.status).toBe(400);
        }
      }
    });

    it('validates deeply nested objects', async () => {
      for (const input of fuzzInputs.structures) {
        const response = await axios.post(`${API_BASE}/api/users`, {
          metadata: input,
          name: 'Test',
          email: 'test@example.com',
        }, { validateStatus: () => true });

        expect(response.status).not.toBe(500);
      }
    });
  });

  describe('GET /api/users/:id - Get User', () => {
    it('handles malformed ID parameters', async () => {
      const idInputs = [
        ...fuzzInputs.strings,
        ...fuzzInputs.sqlInjection,
        ...fuzzInputs.special,
      ];

      for (const input of idInputs) {
        const response = await axios.get(
          `${API_BASE}/api/users/${encodeURIComponent(input)}`,
          { validateStatus: () => true }
        );

        expect(response.status).not.toBe(500);
        // Should be 400 (bad request) or 404 (not found)
        expect([400, 404]).toContain(response.status);
      }
    });
  });

  describe('Query Parameter Fuzzing', () => {
    it('handles malformed query parameters', async () => {
      for (const input of fuzzInputs.strings) {
        const response = await axios.get(`${API_BASE}/api/users`, {
          params: { search: input },
          validateStatus: () => true,
        });

        expect(response.status).not.toBe(500);
      }
    });

    it('prevents injection via query params', async () => {
      for (const payload of fuzzInputs.sqlInjection) {
        const response = await axios.get(`${API_BASE}/api/users`, {
          params: { filter: payload },
          validateStatus: () => true,
        });

        expect(response.status).not.toBe(500);
        // Should not return all users or execute SQL
        if (response.status === 200) {
          expect(response.data.length).toBe(0); // No results for invalid filter
        }
      }
    });
  });
});
```

### Python REST-Assured Fuzzer

```python
# tests/test_api_fuzzer.py
import pytest
import requests
from typing import Any, List
import string
import random

API_BASE = "http://localhost:3000"

class FuzzInputGenerator:
    """Generate various fuzz inputs for API testing"""

    @staticmethod
    def string_mutations() -> List[Any]:
        return [
            "",  # Empty
            None,
            " ",  # Whitespace
            "A" * 10000,  # Very long
            "<script>alert(1)</script>",  # XSS
            "${7*7}",  # Template injection
            "../../etc/passwd",  # Path traversal
            "\x00",  # Null byte
        ]

    @staticmethod
    def sql_injection_payloads() -> List[str]:
        return [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "1; DROP TABLE users--",
            "admin'--",
        ]

    @staticmethod
    def number_mutations() -> List[Any]:
        return [
            0, -1, 999999999999999999,
            -999999999999999999,
            float('inf'), float('-inf'),
        ]

    @staticmethod
    def generate_random_string(length: int = 100) -> str:
        """Generate random string with special characters"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(chars) for _ in range(length))

class TestAPIFuzzing:
    """Comprehensive API fuzz tests"""

    def test_string_input_handling(self):
        """Test API handles malformed string inputs"""
        for input_value in FuzzInputGenerator.string_mutations():
            response = requests.post(
                f"{API_BASE}/api/users",
                json={"name": input_value, "email": "test@example.com"},
                timeout=5
            )

            # Should not crash (500)
            assert response.status_code < 500, \
                f"Server error with input: {repr(input_value)}"

            # Should return proper error for invalid input
            if response.status_code >= 400:
                assert "error" in response.json()

    def test_sql_injection_prevention(self):
        """Test API prevents SQL injection"""
        for payload in FuzzInputGenerator.sql_injection_payloads():
            response = requests.post(
                f"{API_BASE}/api/users",
                json={"name": payload, "email": payload},
                timeout=5
            )

            # Should reject malicious input
            assert response.status_code != 200, \
                f"Accepted SQL injection: {payload}"

            # Should not leak database errors
            if response.status_code >= 400:
                error_text = response.text.lower()
                assert "sql" not in error_text
                assert "database" not in error_text

    def test_numeric_boundary_values(self):
        """Test numeric input boundaries"""
        for value in FuzzInputGenerator.number_mutations():
            response = requests.post(
                f"{API_BASE}/api/users",
                json={
                    "name": "Test User",
                    "email": "test@example.com",
                    "age": value
                },
                timeout=5
            )

            assert response.status_code < 500

    def test_random_fuzzing(self):
        """Random fuzz testing with generated inputs"""
        for _ in range(100):  # 100 random tests
            random_data = {
                "name": FuzzInputGenerator.generate_random_string(random.randint(1, 1000)),
                "email": FuzzInputGenerator.generate_random_string(20),
                "age": random.randint(-1000, 1000),
            }

            response = requests.post(
                f"{API_BASE}/api/users",
                json=random_data,
                timeout=5
            )

            # Should handle gracefully
            assert response.status_code < 500

    def test_header_injection(self):
        """Test header injection vulnerabilities"""
        malicious_headers = {
            "X-Forwarded-For": "' OR '1'='1",
            "User-Agent": "<script>alert(1)</script>",
            "Referer": "javascript:alert(1)",
        }

        response = requests.get(
            f"{API_BASE}/api/users",
            headers=malicious_headers,
            timeout=5
        )

        assert response.status_code < 500
```

## Example Usage

### Example 1: Automated Fuzzing in CI/CD

```javascript
// .github/workflows/fuzz-tests.yml
name: API Fuzz Testing

on: [push, pull_request]

jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start API server
        run: npm run start:test &
      - name: Wait for API
        run: npx wait-on http://localhost:3000/health
      - name: Run fuzz tests
        run: npm run test:fuzz
      - name: Upload fuzz report
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: fuzz-report
          path: ./fuzz-report.html
```

### Example 2: Custom Fuzzer with OpenAPI Spec

```javascript
// fuzzer/openapi-fuzzer.js
const SwaggerParser = require('@apidevtools/swagger-parser');
const axios = require('axios');

async function fuzzFromOpenAPI(specPath) {
  const api = await SwaggerParser.validate(specPath);

  for (const [path, methods] of Object.entries(api.paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      if (method === 'get' || method === 'post') {
        console.log(`Fuzzing ${method.toUpperCase()} ${path}`);

        // Generate fuzz inputs based on parameters
        const fuzzInputs = generateFuzzInputs(operation.parameters);

        for (const input of fuzzInputs) {
          const response = await axios[method](
            `${api.servers[0].url}${path}`,
            input,
            { validateStatus: () => true }
          );

          if (response.status === 500) {
            console.error(`CRASH FOUND: ${method} ${path}`, input);
          }
        }
      }
    }
  }
}

function generateFuzzInputs(parameters) {
  // Generate based on parameter schemas
  return [
    /* fuzz inputs */
  ];
}

fuzzFromOpenAPI('./openapi.yaml');
```

### Example 3: Continuous Fuzzing with AFL-inspired Approach

```python
# fuzzer/continuous_fuzzer.py
import requests
import random
import json
from datetime import datetime

class ContinuousFuzzer:
    """Continuously fuzz API endpoints with mutations"""

    def __init__(self, base_url: str, endpoints: list):
        self.base_url = base_url
        self.endpoints = endpoints
        self.crashes = []

    def mutate_string(self, s: str) -> str:
        """Mutate string with random changes"""
        mutations = [
            lambda x: x + chr(random.randint(0, 255)),  # Append random char
            lambda x: x[:len(x)//2],  # Truncate
            lambda x: x * 100,  # Repeat
            lambda x: x.replace('a', '<script>'),  # XSS injection
            lambda x: x + "' OR '1'='1",  # SQL injection
        ]
        return random.choice(mutations)(s)

    def fuzz_endpoint(self, endpoint: str, method: str = "POST"):
        """Fuzz single endpoint"""
        seed_data = {"name": "test", "email": "test@test.com"}

        for _ in range(1000):  # 1000 iterations
            # Mutate seed data
            fuzzed_data = {}
            for key, value in seed_data.items():
                if isinstance(value, str):
                    fuzzed_data[key] = self.mutate_string(value)
                else:
                    fuzzed_data[key] = value

            # Send request
            try:
                response = requests.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    json=fuzzed_data,
                    timeout=5
                )

                # Detect crashes
                if response.status_code == 500:
                    self.crashes.append({
                        "endpoint": endpoint,
                        "input": fuzzed_data,
                        "response": response.text,
                        "timestamp": datetime.now().isoformat()
                    })

            except requests.exceptions.Timeout:
                # Potential hang/DoS
                self.crashes.append({
                    "endpoint": endpoint,
                    "input": fuzzed_data,
                    "error": "timeout",
                    "timestamp": datetime.now().isoformat()
                })

    def run(self, duration_minutes: int = 60):
        """Run continuous fuzzing"""
        import time
        start_time = time.time()

        while (time.time() - start_time) < (duration_minutes * 60):
            endpoint = random.choice(self.endpoints)
            self.fuzz_endpoint(endpoint)

        # Save crash report
        with open('crash_report.json', 'w') as f:
            json.dump(self.crashes, f, indent=2)

        print(f"Found {len(self.crashes)} crashes")

# Usage
fuzzer = ContinuousFuzzer(
    base_url="http://localhost:3000",
    endpoints=["/api/users", "/api/orders", "/api/products"]
)
fuzzer.run(duration_minutes=60)
```

## Error Handling

**Common issues and solutions:**

**Problem**: Fuzzer overwhelms API with requests
- **Cause**: No rate limiting in fuzzer
- **Solution**: Add delays between requests, respect API rate limits

**Problem**: False positives (valid errors reported as crashes)
- **Cause**: Fuzzer doesn't understand expected behavior
- **Solution**: Define expected error codes (400, 404), only flag 500s as crashes

**Problem**: Fuzzer credentials get rate-limited or blocked
- **Cause**: Too many failed auth attempts
- **Solution**: Use test credentials, whitelist test IPs, reset between runs

**Problem**: Fuzzing breaks production data
- **Cause**: Fuzzer running against production environment
- **Solution**: Always fuzz staging/test environments, use test data

**Problem**: Can't reproduce crashes
- **Cause**: Fuzzer doesn't log exact inputs that caused crashes
- **Solution**: Log all inputs, responses, timestamps for crash reproduction

## Configuration

### Fuzzer Configuration File

```javascript
// fuzzer.config.js
module.exports = {
  target: {
    baseUrl: process.env.API_URL || 'http://localhost:3000',
    endpoints: [
      { path: '/api/users', method: 'POST' },
      { path: '/api/users/:id', method: 'GET' },
      { path: '/api/orders', method: 'POST' },
    ],
  },

  authentication: {
    type: 'bearer', // 'bearer' | 'basic' | 'apiKey'
    token: process.env.TEST_API_TOKEN,
  },

  fuzzing: {
    iterations: 1000, // Tests per endpoint
    timeout: 5000, // Request timeout (ms)
    delay: 100, // Delay between requests (ms)
    concurrent: 5, // Concurrent requests
  },

  inputs: {
    strings: true, // Enable string fuzzing
    numbers: true, // Enable number fuzzing
    sqlInjection: true, // Enable SQL injection tests
    xss: true, // Enable XSS tests
    customPayloads: [ // Custom payloads
      '{{7*7}}',
      '${7*7}',
    ],
  },

  reporting: {
    output: './fuzz-report.html',
    verbose: false,
    onCrash: (crash) => {
      console.error('CRASH:', crash);
      // Send alert (Slack, PagerDuty, etc.)
    },
  },

  skipEndpoints: [
    '/api/health', // Skip health checks
    '/api/metrics', // Skip metrics
  ],
};
```

## Best Practices

DO:
- Run fuzzing in staging/test environments, never production
- Log all crash-inducing inputs for reproducibility
- Integrate fuzzing into CI/CD pipeline
- Fuzz high-risk endpoints (auth, payment, admin) more thoroughly
- Use realistic seed data (from production, anonymized)
- Monitor API during fuzzing for crashes and anomalies
- Combine fuzzing with other security testing (SAST, DAST, pen testing)

DON'T:
- Fuzz production APIs without explicit permission
- Use production credentials or test accounts in fuzzer
- Ignore 400-level errors (they might indicate security issues)
- Run unbounded fuzzing (set time/iteration limits)
- Skip regression tests after fixing fuzz-discovered bugs
- Overlook API dependencies (databases, external APIs)

TIPS:
- Start with known payloads (OWASP, SecLists) before random fuzzing
- Use OpenAPI specs to auto-generate fuzz tests
- Combine grammar-based and mutation-based fuzzing
- Monitor server logs, not just HTTP responses
- Fuzz at multiple levels (headers, body, query params, path params)
- Use corpus of real user inputs as seed data

## Related Commands

- `/scan-api-security` - Comprehensive security scanning
- `/validate-schemas` - Schema validation testing
- `/run-load-test` - Performance testing under load
- `/generate-rest-api` - Generate APIs with built-in validation
- `/implement-error-handling` - Proper error handling to prevent info leaks

## Performance Considerations

- **Fuzzing throughput**: 100-1000 requests/sec depending on API complexity
- **Coverage**: Aim for 80%+ code coverage with fuzz tests
- **Duration**: Run continuous fuzzing (1+ hours) to find rare bugs
- **Resource usage**: Monitor CPU/memory during fuzzing to detect leaks

**Optimization strategies:**
- Use parallel fuzzing with multiple workers
- Cache API responses to avoid redundant tests
- Prioritize high-risk endpoints for deeper fuzzing
- Use smart fuzzing (AFL-style coverage guidance)

## Security Considerations

- **Authorization**: Fuzz with different permission levels (guest, user, admin)
- **Rate limiting**: Verify fuzzing doesn't bypass rate limits
- **Logging**: Ensure malicious inputs are logged for security monitoring
- **Secrets**: Never log sensitive data (passwords, tokens) from fuzz inputs
- **Compliance**: Document fuzzing for security compliance (SOC 2, ISO 27001)

**Security checklist:**
- [ ] Fuzz authentication endpoints (login, register, password reset)
- [ ] Test authorization bypass (accessing other users' data)
- [ ] Validate input sanitization (XSS, SQL injection)
- [ ] Check file upload endpoints (malicious files, XXE)
- [ ] Test CSRF protection
- [ ] Verify error messages don't leak sensitive info

## Troubleshooting

**Fuzzer hangs or times out:**
1. Increase request timeout setting
2. Check for infinite loops in API code
3. Monitor API server resources (CPU, memory)
4. Reduce concurrent fuzzing requests

**No crashes found:**
1. Verify API is actually receiving fuzz inputs
2. Check if input validation is too strict (rejecting all fuzz inputs)
3. Increase fuzzing iterations
4. Use smarter fuzzing strategies (grammar-based, mutation-based)

**Too many false positives:**
1. Define expected error codes (400, 404, 401, 403)
2. Only flag 500-level errors as crashes
3. Review API logs to understand error causes
4. Adjust fuzzer configuration

**Can't reproduce crashes:**
1. Ensure fuzzer logs exact inputs that caused crashes
2. Check if crash is timing-dependent (race condition)
3. Verify environment matches (same data, same config)
4. Use deterministic fuzzing (fixed seed) for reproducibility

## Version History

- **1.0.0** (2025-10-11): Initial release with comprehensive fuzzing
  - String, number, SQL, XSS payload generation
  - Jest and pytest test suites
  - OpenAPI-driven fuzzing
  - Continuous fuzzing with crash detection
  - CI/CD integration examples
  - Security best practices and checklist
