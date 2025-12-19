---
name: generating-unit-tests
version: 1.0.0
description: |
  Automatically generate comprehensive unit tests from source code covering happy paths, edge cases, and error conditions.
  Use when creating test coverage for functions, classes, or modules.
  Trigger with phrases like "generate unit tests", "create tests for", or "add test coverage".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:unit-*)
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
## Prerequisites

Before using this skill, ensure you have:
- Source code files requiring test coverage
- Testing framework installed (Jest, Mocha, pytest, JUnit, etc.)
- Understanding of code dependencies and external services to mock
- Test directory structure established (e.g., `tests/`, `__tests__/`, `spec/`)
- Package configuration updated with test scripts

## Instructions

### Step 1: Analyze Source Code
Examine code structure and identify test requirements:
1. Use Read tool to load source files from {baseDir}/src/
2. Identify all functions, classes, and methods requiring tests
3. Document function signatures, parameters, return types, and side effects
4. Note external dependencies requiring mocking or stubbing

### Step 2: Determine Testing Framework
Select appropriate testing framework based on language:
- JavaScript/TypeScript: Jest, Mocha, Jasmine, Vitest
- Python: pytest, unittest, nose2
- Java: JUnit 5, TestNG
- Go: testing package with testify assertions
- Ruby: RSpec, Minitest

### Step 3: Generate Test Cases
Create comprehensive test suite covering:
1. Happy path tests with valid inputs and expected outputs
2. Edge case tests with boundary values (empty arrays, null, zero, max values)
3. Error condition tests with invalid inputs
4. Mock external dependencies (databases, APIs, file systems)
5. Setup and teardown fixtures for test isolation

### Step 4: Write Test File
Generate test file in {baseDir}/tests/ with structure:
- Import statements for code under test and testing framework
- Mock declarations for external dependencies
- Describe/context blocks grouping related tests
- Individual test cases with arrange-act-assert pattern
- Cleanup logic in afterEach/tearDown hooks

## Output

The skill generates complete test files:

### Test File Structure
```javascript
// Example Jest test file
import { validator } from '../src/utils/validator';

describe('Validator', () => {
  describe('validateEmail', () => {
    it('should accept valid email addresses', () => {
      expect(validator.validateEmail('test@example.com')).toBe(true);
    });

    it('should reject invalid email formats', () => {
      expect(validator.validateEmail('invalid-email')).toBe(false);
    });

    it('should handle null and undefined', () => {
      expect(validator.validateEmail(null)).toBe(false);
      expect(validator.validateEmail(undefined)).toBe(false);
    });
  });
});
```

### Coverage Metrics
- Line coverage percentage (target: 80%+)
- Branch coverage showing tested conditional paths
- Function coverage ensuring all exports are tested
- Statement coverage for comprehensive validation

### Mock Implementations
Generated mocks for:
- Database connections and queries
- HTTP requests to external APIs
- File system operations (read/write)
- Environment variables and configuration
- Time-dependent functions (Date.now(), setTimeout)

## Error Handling

Common issues and solutions:

**Module Import Errors**
- Error: Cannot find module or dependencies
- Solution: Install missing packages; verify import paths match project structure; check TypeScript configuration

**Mock Setup Failures**
- Error: Mock not properly intercepting calls
- Solution: Ensure mocks are defined before imports; use proper mocking syntax for framework; clear mocks between tests

**Async Test Timeouts**
- Error: Test exceeded timeout before completing
- Solution: Increase timeout for slow operations; ensure async/await or done callbacks are used correctly; check for unresolved promises

**Test Isolation Issues**
- Error: Tests pass individually but fail when run together
- Solution: Add proper cleanup in afterEach hooks; avoid shared mutable state; reset mocks between tests

## Resources

### Testing Frameworks
- Jest documentation for JavaScript testing
- pytest documentation for Python testing
- JUnit 5 User Guide for Java testing
- Go testing package and testify library

### Best Practices
- Follow AAA pattern (Arrange, Act, Assert) for test structure
- Write tests before fixing bugs (test-driven bug fixing)
- Use descriptive test names that explain the scenario
- Keep tests independent and avoid test interdependencies
- Mock external dependencies for unit test isolation
- Aim for 80%+ code coverage on critical paths