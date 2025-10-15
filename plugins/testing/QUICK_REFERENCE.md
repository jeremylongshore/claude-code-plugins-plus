# Testing Suite - Quick Reference Card

**10 Professional Testing Plugins for Complete QA Coverage**

---

## Command Shortcuts

```bash
/gut         # Generate unit tests
/rit         # Run integration tests
/e2e         # Generate E2E tests
/cov         # Analyze code coverage
/reg         # Track regression tests
```

## Agent Activation (Auto)

Simply mention these topics and the agent activates:

- **API testing** → api-test-automation
- **Performance testing** → performance-test-suite
- **Security scanning** → security-test-scanner
- **Test quality** → mutation-test-runner
- **Test data** → test-data-generator

---

## Quick Usage Examples

### Generate Unit Tests
```
/gut src/utils/validator.js
Generate unit tests for the user authentication module
```

### Run Integration Tests
```
/rit
/rit --coverage
Run integration tests for the API
```

### API Testing
```
Generate API tests for the user management endpoints
Create tests for the GraphQL API with authentication
```

### Performance Testing
```
Create a load test ramping up to 500 concurrent users
Design a stress test to find the API breaking point
```

### Security Testing
```
Run security scan on the authentication system
Test for SQL injection vulnerabilities in the search endpoint
Check for OWASP Top 10 vulnerabilities
```

### E2E Testing
```
/e2e
Generate E2E tests for the checkout workflow
Create Playwright tests for user registration
```

### Coverage Analysis
```
/cov
/cov --threshold 80
Analyze test coverage and identify gaps
```

### Mutation Testing
```
Run mutation testing on the validator module
Check test quality with mutation testing
```

### Regression Testing
```
/reg
Mark this test as a regression test
Run the regression suite before deployment
```

### Test Data Generation
```
Generate 100 test users with addresses
Create e-commerce test data (products, orders, customers)
Generate realistic test data for the API
```

---

## Installation

```bash
# Add marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install all testing plugins
/plugin install unit-test-generator@claude-code-plugins-plus
/plugin install integration-test-runner@claude-code-plugins-plus
/plugin install api-test-automation@claude-code-plugins-plus
/plugin install performance-test-suite@claude-code-plugins-plus
/plugin install security-test-scanner@claude-code-plugins-plus
/plugin install e2e-test-framework@claude-code-plugins-plus
/plugin install test-coverage-analyzer@claude-code-plugins-plus
/plugin install mutation-test-runner@claude-code-plugins-plus
/plugin install regression-test-tracker@claude-code-plugins-plus
/plugin install test-data-generator@claude-code-plugins-plus
```

---

## Testing Workflow

### 1️⃣ Development
```bash
/gut src/module.js           # Generate unit tests
Generate test data           # Create fixtures
npm test                     # Run tests
```

### 2️⃣ Integration
```bash
/rit                         # Integration tests
Generate API tests           # API endpoint tests
```

### 3️⃣ Pre-Deployment
```bash
/reg                         # Regression suite
Security scan                # Vulnerability check
Performance test             # Load testing
/e2e                         # E2E workflows
```

### 4️⃣ Quality Assurance
```bash
/cov --threshold 80          # Coverage check
Mutation testing             # Test quality
```

---

## Plugin Matrix

| Plugin | Type | Shortcut | Use Case |
|--------|------|----------|----------|
| Unit Test Generator | Cmd | `/gut` | Generate unit tests |
| Integration Test Runner | Cmd | `/rit` | Run integration tests |
| API Test Automation | Agent | Auto | API endpoint testing |
| Performance Test Suite | Agent | Auto | Load/stress testing |
| Security Test Scanner | Agent | Auto | Vulnerability scanning |
| E2E Test Framework | Cmd | `/e2e` | Browser testing |
| Test Coverage Analyzer | Cmd | `/cov` | Coverage analysis |
| Mutation Test Runner | Agent | Auto | Test quality validation |
| Regression Test Tracker | Cmd | `/reg` | Regression testing |
| Test Data Generator | Agent | Auto | Generate test data |

---

## Framework Support

- **JavaScript/TypeScript**: Jest, Playwright, Cypress, k6, Stryker
- **Python**: pytest, Locust, mutmut
- **Java**: JUnit, Gatling, PITest
- **Go**: testing, httptest
- **Ruby**: RSpec, Minitest
- **C#**: xUnit, NUnit
- **PHP**: PHPUnit

---

## Quality Targets

- **Code Coverage**: 80%+
- **Mutation Score**: 80%+
- **Performance P95**: < 300ms
- **Performance P99**: < 500ms
- **Security**: Zero critical vulnerabilities
- **Regression Pass Rate**: 100%

---

## Tips

1. Start with unit tests (test pyramid base)
2. Use realistic test data
3. Run regression tests before every deploy
4. Security test regularly, not just pre-release
5. Performance test early and often
6. Track coverage trends over time
7. Use mutation testing to validate test quality
8. Automate everything in CI/CD

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Total Plugins**: 10
