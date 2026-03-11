---
name: generating-unit-tests
description: |
  Test automatically generate comprehensive unit tests from source code covering happy paths, edge cases, and error conditions.
  Use when creating test coverage for functions, classes, or modules.
  Trigger with phrases like "generate unit tests", "create tests for", or "add test coverage".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:unit-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Unit Test Generator

## Overview

Automatically generate comprehensive unit tests from source code analysis covering happy paths, edge cases, boundary conditions, and error handling. Supports Jest, Vitest, Mocha (JavaScript/TypeScript), pytest (Python), JUnit 5 (Java), and Go testing with testify.

## Prerequisites

- Testing framework installed and configured (`jest`, `vitest`, `pytest`, `junit-jupiter`, or Go `testing`)
- Source code with clear function signatures, type annotations, or JSDoc comments
- Test directory structure established (`__tests__/`, `tests/`, `spec/`, or `*_test.go`)
- Mocking library available (`jest.mock`, `unittest.mock`, `Mockito`, or `gomock`)
- Package scripts configured to run tests (`npm test`, `pytest`, `go test`)

## Instructions

1. Scan the codebase with Glob to locate source files that lack corresponding test files (e.g., `src/utils/parser.ts` without `__tests__/parser.test.ts`).
2. Read each untested source file and extract:
   - All exported functions and class methods with their signatures.
   - Parameter types, return types, and thrown exceptions.
   - External dependencies (imports from other modules, third-party libraries, I/O).
   - Pure vs. impure function classification.
3. For each function, generate test cases in these categories:
   - **Happy path**: Valid inputs producing expected outputs (at least 2 cases).
   - **Edge cases**: Empty strings, empty arrays, zero, negative numbers, `null`, `undefined`, maximum values.
   - **Error conditions**: Invalid types, missing required fields, network failures, permission errors.
   - **Boundary values**: Off-by-one, integer overflow, string length limits.
4. Create mock declarations for all external dependencies:
   - Database calls return predictable fixture data.
   - HTTP clients return canned responses with configurable status codes.
   - File system operations use in-memory buffers or temp directories.
5. Write the test file following project conventions:
   - Match the existing test file naming pattern (`*.test.ts`, `*.spec.js`, `test_*.py`).
   - Group tests in `describe`/`context` blocks by function name.
   - Use `beforeEach`/`afterEach` for setup and teardown.
   - Include inline comments explaining non-obvious test rationale.
6. Run the generated tests to verify they pass, then check coverage to confirm the target function is fully exercised.
7. Report coverage gaps and suggest additional test cases for uncovered branches.

## Output

- Test files placed alongside source files or in the project's test directory
- Mock/stub files for external dependencies
- Coverage report showing line, branch, and function coverage for tested modules
- List of remaining coverage gaps with suggested test cases

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Cannot find module` on import | Test file path does not match project module resolution | Check `tsconfig.json` paths and `moduleNameMapper` in Jest config |
| Mock not intercepting calls | Mock defined after module import caches the real implementation | Move `jest.mock()` calls to the top of the file before any imports |
| Async test timeout | Promise never resolves due to missing `await` or unhandled rejection | Add `await` before async calls; increase timeout with `jest.setTimeout()` |
| Tests pass alone but fail together | Shared mutable state leaking between tests | Reset state in `afterEach`; avoid module-level variables; use `jest.isolateModules()` |
| Snapshot mismatch on first run | No existing snapshot baseline | Run with `--updateSnapshot` on first execution to create the baseline |

## Examples

**Jest test for a string utility:**
```typescript
import { slugify } from '../src/utils/slugify';

describe('slugify', () => {
  it('converts spaces to hyphens', () => {
    expect(slugify('hello world')).toBe('hello-world');
  });
  it('lowercases all characters', () => {
    expect(slugify('Hello World')).toBe('hello-world');
  });
  it('removes special characters', () => {
    expect(slugify('hello@world!')).toBe('helloworld');
  });
  it('handles empty string', () => {
    expect(slugify('')).toBe('');
  });
  it('trims leading and trailing whitespace', () => {
    expect(slugify('  spaced  ')).toBe('spaced');
  });
});
```

**pytest test for a data validator:**
```python
import pytest
from myapp.validators import validate_email

class TestValidateEmail:
    def test_accepts_valid_email(self):
        assert validate_email("user@example.com") is True

    def test_rejects_missing_at_sign(self):
        assert validate_email("userexample.com") is False

    def test_rejects_empty_string(self):
        assert validate_email("") is False

    def test_rejects_none(self):
        with pytest.raises(TypeError):
            validate_email(None)
```

## Resources

- Jest documentation: https://jestjs.io/docs/getting-started
- Vitest documentation: https://vitest.dev/guide/
- pytest documentation: https://docs.pytest.org/
- JUnit 5 User Guide: https://junit.org/junit5/docs/current/user-guide/
- Go testing package: https://pkg.go.dev/testing
- AAA pattern (Arrange-Act-Assert): https://automationpanda.com/2020/07/07/arrange-act-assert-pattern-for-python-unit-tests/