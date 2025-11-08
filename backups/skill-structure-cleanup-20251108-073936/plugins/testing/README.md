# Testing Suite Plugins

A comprehensive collection of 10 professional testing plugins covering all aspects of software quality assurance.

## Overview

This testing suite provides complete test automation coverage from unit tests to end-to-end workflows, security scanning, performance testing, and test quality validation.

## Plugin Collection

### 1. Unit Test Generator
**Generate comprehensive unit tests from source code**

- Multi-framework support (Jest, pytest, JUnit, etc.)
- Happy paths, edge cases, error handling
- Mock generation for external dependencies
- Shortcut: `/gut`

[View Plugin](./unit-test-generator/)

---

### 2. Integration Test Runner
**Run integration test suites with automated setup and teardown**

- Database preparation and seeding
- Service orchestration (Docker, Redis, queues)
- Environment management
- Comprehensive reporting
- Shortcut: `/rit`

[View Plugin](./integration-test-runner/)

---

### 3. API Test Automation
**Automated REST and GraphQL API endpoint testing**

- REST API testing (CRUD operations)
- GraphQL testing (queries, mutations, subscriptions)
- Authentication testing (JWT, OAuth, API keys)
- Contract testing against OpenAPI/Swagger
- Agent-based (activates automatically)

[View Plugin](./api-test-automation/)

---

### 4. Performance Test Suite
**Load testing, stress testing, and performance benchmarking**

- Load testing (gradual ramp-up)
- Stress testing (find breaking points)
- Spike testing (sudden traffic surges)
- Endurance testing (memory leak detection)
- Metrics analysis (P95, P99 percentiles)
- Bottleneck identification
- Agent-based (activates automatically)

[View Plugin](./performance-test-suite/)

---

### 5. Security Test Scanner
**OWASP Top 10 and security vulnerability testing**

- SQL injection, XSS, CSRF testing
- Authentication and authorization testing
- Security misconfiguration detection
- OWASP Top 10 coverage
- Comprehensive security reports
- Agent-based (activates automatically)

[View Plugin](./security-test-scanner/)

---

### 6. E2E Test Framework
**Browser-based end-to-end test automation**

- Playwright, Cypress, Selenium support
- User workflow testing
- Page Object Model patterns
- Cross-browser testing
- Mobile emulation
- Shortcut: `/e2e`

[View Plugin](./e2e-test-framework/)

---

### 7. Test Coverage Analyzer
**Analyze code coverage and identify untested code**

- Line, branch, function, statement coverage
- Uncovered code identification
- Coverage trends over time
- Threshold enforcement
- Detailed per-file reports
- Shortcut: `/cov`

[View Plugin](./test-coverage-analyzer/)

---

### 8. Mutation Test Runner
**Validate test quality through mutation testing**

- Code mutation generation
- Test effectiveness validation
- Mutation score calculation
- Survivor analysis
- Framework support (Stryker, PITest, mutmut)
- Agent-based (activates automatically)

[View Plugin](./mutation-test-runner/)

---

### 9. Regression Test Tracker
**Track and run regression tests for stability**

- Critical test tracking
- Automated execution before deployments
- Change impact analysis
- Flaky test detection
- Test history and trends
- Shortcut: `/reg`

[View Plugin](./regression-test-tracker/)

---

### 10. Test Data Generator
**Generate realistic test data for comprehensive testing**

- User data (names, emails, addresses)
- Business data (products, orders, invoices)
- Technical data (UUIDs, IPs, tokens)
- Custom schema support (JSON Schema, TypeScript)
- Bulk generation
- Locale support
- Agent-based (activates automatically)

[View Plugin](./test-data-generator/)

---

## Installation

Install individual plugins:

```bash
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

## Quick Reference

| Plugin | Type | Shortcut | Primary Use |
|--------|------|----------|-------------|
| Unit Test Generator | Command | `/gut` | Generate unit tests |
| Integration Test Runner | Command | `/rit` | Run integration tests |
| API Test Automation | Agent | Auto | API endpoint testing |
| Performance Test Suite | Agent | Auto | Load/stress testing |
| Security Test Scanner | Agent | Auto | Security scanning |
| E2E Test Framework | Command | `/e2e` | Browser testing |
| Test Coverage Analyzer | Command | `/cov` | Coverage analysis |
| Mutation Test Runner | Agent | Auto | Test quality validation |
| Regression Test Tracker | Command | `/reg` | Regression testing |
| Test Data Generator | Agent | Auto | Test data creation |

## Testing Workflow

### 1. Development Phase
```bash
# Generate unit tests
/gut src/utils/validator.js

# Generate test data
"Generate 50 test users with addresses"

# Run tests with coverage
/cov
```

### 2. Integration Phase
```bash
# Run integration tests
/rit

# Test APIs
"Generate API tests for user endpoints"
```

### 3. Pre-deployment Phase
```bash
# Run regression suite
/reg

# Security scan
"Run security vulnerability scan on authentication system"

# Performance test
"Create load test for API with 500 concurrent users"
```

### 4. Quality Assurance
```bash
# E2E tests
/e2e

# Check test quality
"Run mutation testing on user service"

# Coverage analysis
/cov --threshold 80
```

## Framework Support

### JavaScript/TypeScript
- **Unit**: Jest, Mocha, Vitest, Jasmine
- **E2E**: Playwright, Cypress, Selenium
- **Performance**: k6, Artillery
- **Coverage**: nyc, c8
- **Mutation**: Stryker

### Python
- **Unit**: pytest, unittest
- **Integration**: pytest with fixtures
- **Performance**: Locust
- **Coverage**: coverage.py
- **Mutation**: mutmut, cosmic-ray

### Java
- **Unit**: JUnit 5, TestNG
- **Integration**: Spring Test, Testcontainers
- **Performance**: Gatling, JMeter
- **Coverage**: JaCoCo
- **Mutation**: PITest

### Other Languages
- **Go**: testing package, Testify
- **Ruby**: RSpec, Minitest
- **C#**: xUnit, NUnit, MSTest
- **PHP**: PHPUnit

## Best Practices

### Test Pyramid
1. **Unit tests** (70%) - Fast, isolated, focused
2. **Integration tests** (20%) - API and service interactions
3. **E2E tests** (10%) - Critical user workflows

### Quality Metrics
- **Code coverage**: 80%+ (but quality > quantity)
- **Mutation score**: 80%+ (validates test effectiveness)
- **Performance**: P95 < 300ms, P99 < 500ms
- **Security**: Zero critical vulnerabilities

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
test:
  - run: npm test              # Unit tests
  - run: /rit                  # Integration tests
  - run: /reg                  # Regression tests
  - run: /cov --threshold 80   # Coverage check

pre-deploy:
  - run: /e2e                  # E2E tests
  - run: Security scan         # Vulnerability scan
  - run: Performance test      # Load test
```

## Tips

1. **Start with unit tests** - Foundation of test pyramid
2. **Use test data generators** - Realistic, varied data
3. **Track regression tests** - Protect critical functionality
4. **Monitor coverage** - Identify gaps
5. **Security test regularly** - Don't wait for production
6. **Performance test early** - Catch issues before scale
7. **Validate test quality** - Use mutation testing
8. **Automate everything** - CI/CD integration

## Resources

- [Testing Best Practices](https://martinfowler.com/testing/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Performance Testing Guidance](https://k6.io/docs/)

## Contributing

To contribute a new testing plugin:

1. Follow the plugin structure in existing plugins
2. Include comprehensive README with examples
3. Add proper keywords for discoverability
4. Test locally before submitting
5. Submit PR with plugin details

## License

All plugins in this suite are licensed under MIT License.

---

**Testing Suite Version**: 1.0.0
**Total Plugins**: 10
**Last Updated**: October 2025
