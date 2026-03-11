---
name: generating-test-doubles
description: |
  Generate mocks, stubs, spies, and fakes for dependency isolation.
  Use when creating mocks, stubs, or test isolation fixtures.
  Trigger with phrases like "generate mocks", "create test doubles", or "setup stubs".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:doubles-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Test Doubles Generator

## Overview

Generate mocks, stubs, spies, and fakes to isolate units under test from external dependencies. Supports Jest mocks, Sinon.js stubs, Python unittest.mock, Go interfaces, and testdouble.js patterns.

## Prerequisites

- Testing framework installed (Jest, Vitest, Mocha, pytest, JUnit 5, or Go testing)
- Mocking library available (Sinon.js, testdouble.js, unittest.mock, Mockito, or gomock)
- TypeScript `strict` mode enabled for type-safe mocks (if applicable)
- Source code with clear interface or class boundaries for dependency injection

## Instructions

1. Scan the codebase with Glob and Grep to identify modules with external dependencies (database clients, HTTP clients, file system access, third-party SDKs).
2. Read each module under test and catalog its dependency interfaces -- list every method signature, return type, and side effect.
3. Determine the appropriate test double type for each dependency:
   - **Stub**: Returns canned data, no behavior verification (use for database queries returning fixed datasets).
   - **Mock**: Verifies interactions -- call count, argument matching, call order (use for email senders, event emitters).
   - **Spy**: Wraps real implementation while recording calls (use when partial behavior is needed).
   - **Fake**: Lightweight working implementation (use for in-memory repositories replacing real databases).
4. Generate test double files following the project's existing test directory structure (e.g., `__mocks__/`, `test/doubles/`, `testutil/`).
5. For each test double, implement:
   - Factory function or class matching the dependency interface exactly.
   - Configurable return values via builder pattern or method chaining.
   - Call recording for assertion (arguments, call count, call order).
   - Reset/restore mechanism for cleanup between tests.
6. Wire test doubles into existing test files using the framework's dependency injection pattern (`jest.mock()`, `@patch`, constructor injection, or Go interface substitution).
7. Validate all test doubles compile and pass type checks by running `tsc --noEmit` or equivalent.

## Output

- Test double source files (one per dependency) placed in the project's mock directory
- Factory functions with TypeScript generics or equivalent type safety
- Jest `__mocks__` auto-mock modules where applicable
- Updated test files wired to use generated doubles instead of real dependencies
- Summary listing each double, its type (mock/stub/spy/fake), and the interface it replaces

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `TypeError: X is not a function` | Mock missing a method from the real interface | Regenerate the double from the current interface definition; add the missing method |
| Mock leaking between tests | Shared mock state not reset in `afterEach` | Add `jest.restoreAllMocks()` or `sinon.restore()` in teardown hooks |
| Type mismatch on mock return value | Return type does not match interface contract | Use `as ReturnType<typeof fn>` or update the mock factory to return the correct type |
| Spy not recording calls | Spy created after the function was already bound | Create spies before the module under test imports the dependency |
| Over-mocking hides real bugs | Too many layers replaced with fakes | Limit mocks to true external boundaries (I/O, network); let pure logic run unmocked |

## Examples

**Jest mock factory for a UserRepository:**
```typescript
// __mocks__/userRepository.ts
export const createMockUserRepo = () => ({
  findById: jest.fn().mockResolvedValue({ id: '1', name: 'Test User' }),
  save: jest.fn().mockResolvedValue(undefined),
  delete: jest.fn().mockResolvedValue(true),
});
```

**Python unittest.mock patch for an HTTP client:**
```python
from unittest.mock import patch, MagicMock

@patch('myapp.client.requests.get')
def test_fetch_data(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"key": "value"})  # HTTP 200 OK
    result = fetch_data("https://api.example.com/data")
    assert result == {"key": "value"}
    mock_get.assert_called_once()
```

**Go interface-based fake:**
```go
type FakeStore struct {
    data map[string]string
}
func (f *FakeStore) Get(key string) (string, error) {
    v, ok := f.data[key]
    if !ok { return "", ErrNotFound }
    return v, nil
}
```

## Resources

- Jest Manual Mocks: https://jestjs.io/docs/manual-mocks
- Sinon.js Stubs, Mocks, Spies: https://sinonjs.org/
- Python unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- Mockito (Java): https://site.mockito.org/
- gomock (Go): https://github.com/uber-go/mock
- Martin Fowler, "Mocks Aren't Stubs": https://martinfowler.com/articles/mocksArentStubs.html