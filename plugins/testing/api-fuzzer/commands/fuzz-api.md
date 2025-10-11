---
description: Fuzz test APIs with malformed inputs and edge cases
shortcut: fuzz
---

# API Fuzzer

Automated fuzz testing for REST APIs to discover vulnerabilities, crashes, and unexpected behavior through malformed inputs, boundary values, and random payloads.

## What You Do

1. **Generate Fuzz Inputs**: Create malformed, boundary, and random test data
2. **Test API Endpoints**: Send fuzz inputs to all API endpoints
3. **Detect Vulnerabilities**: Identify crashes, errors, and security issues
4. **Report Findings**: Document discovered issues with reproducible examples

## Output Example

```javascript
// Fuzz test configuration
const fuzzTests = {
  stringInputs: ['', null, undefined, '<script>alert(1)</script>', 'A'.repeat(10000)],
  numberInputs: [0, -1, Infinity, -Infinity, NaN, Number.MAX_SAFE_INTEGER],
  sqlInjection: ["' OR '1'='1", "1; DROP TABLE users--"],
  xss: ['<img src=x onerror=alert(1)>', '<svg/onload=alert(1)>']
};

describe('API Fuzzing', () => {
  it('handles malformed inputs gracefully', async () => {
    for (const input of fuzzTests.stringInputs) {
      const response = await api.post('/user', { name: input });
      expect(response.status).not.toBe(500); // No crashes
      expect(response.status).toBeLessThan(500); // Proper error handling
    }
  });
});
```
