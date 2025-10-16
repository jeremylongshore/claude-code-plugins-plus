---
name: Test Generator
description: Automatically generates unit tests, integration tests, and test cases when user mentions testing, test coverage, or needs tests written. Supports multiple testing frameworks and languages.
allowed-tools: Read, Write, Grep
---

# Test Generator

## Purpose
Automatically generates comprehensive test suites for code including unit tests, integration tests, edge cases, and test data. Supports Jest, pytest, JUnit, RSpec, and more.

## Trigger Keywords
- "generate tests"
- "write tests"
- "test coverage"
- "unit test"
- "integration test"
- "need tests"
- "test cases"
- "testing"

## Generation Process

When activated, I will:

1. **Analyze the code** to understand:
   - Functions and methods to test
   - Input/output types
   - Edge cases and boundaries
   - Dependencies and mocking needs

2. **Generate test cases** covering:
   - Happy path scenarios
   - Edge cases (null, empty, max values)
   - Error conditions
   - Boundary values
   - Integration points

3. **Create test files** with:
   - Proper imports and setup
   - Descriptive test names
   - Arrange-Act-Assert structure
   - Mock configurations
   - Cleanup/teardown

4. **Calculate coverage** and suggest additional tests if needed

## Supported Frameworks

**JavaScript/TypeScript:**
- Jest
- Mocha + Chai
- Vitest

**Python:**
- pytest
- unittest

**Java:**
- JUnit 5
- TestNG

**Ruby:**
- RSpec
- Minitest

**Go:**
- testing package
- testify

## Test Structure

I generate tests following best practices:

```javascript
describe('ComponentName', () => {
  describe('methodName', () => {
    it('should handle happy path correctly', () => {
      // Arrange
      const input = {...}

      // Act
      const result = method(input)

      // Assert
      expect(result).toBe(expected)
    })

    it('should handle edge case: null input', () => {
      // Test null handling
    })

    it('should throw error when invalid', () => {
      // Test error cases
    })
  })
})
```

## Output Format

I provide:
- Complete test file with all imports
- Test data and fixtures
- Mock configurations
- Expected vs actual assertions
- Coverage report summary

## Examples

**User says:** "Generate tests for the UserService class"

**I automatically:**
1. Read UserService code
2. Identify all methods
3. Generate comprehensive test suite
4. Include mocks for dependencies
5. Create test file in appropriate directory

**User says:** "Need test coverage for this function"

**I automatically:**
1. Analyze function complexity
2. Identify all code paths
3. Generate tests for each path
4. Add edge case tests
5. Report coverage percentage
