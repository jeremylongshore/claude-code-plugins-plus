# Unit Test Generator Plugin

Automatically generate comprehensive unit tests from source code with intelligent framework detection and best practices.

## Features

- **Multi-framework support** - Jest, pytest, JUnit, Go testing, RSpec, and more
- **Intelligent test generation** - Analyzes code to create relevant test cases
- **Complete coverage** - Happy paths, edge cases, error handling
- **Mock generation** - Automatic mocking of external dependencies
- **Best practices** - Arrange-Act-Assert, descriptive names, proper structure

## Installation

```bash
/plugin install unit-test-generator@claude-code-plugins-plus
```

## Usage

### Generate tests for a file

```bash
/generate-tests src/utils/validator.js
```

### Specify framework explicitly

```bash
/generate-tests --framework pytest src/api/users.py
```

### Use shortcut

```bash
/gut models/UserModel.ts
```

## What Gets Generated

The plugin creates test files with:

1. **Proper imports and setup** - Framework-specific boilerplate
2. **Test suite organization** - Logical grouping of related tests
3. **Comprehensive test cases**:
   - Valid inputs (typical scenarios)
   - Invalid inputs (null, undefined, wrong types)
   - Boundary conditions (limits, empty collections)
   - Error scenarios (exceptions, failures)
   - State changes (when applicable)
4. **Mocks and stubs** - For external dependencies
5. **Clear assertions** - Validating expected outcomes
6. **Helpful comments** - Explaining complex scenarios

## Supported Languages & Frameworks

| Language | Frameworks |
|----------|------------|
| JavaScript/TypeScript | Jest, Mocha, Vitest, Jasmine |
| Python | pytest, unittest, nose2 |
| Java | JUnit 5, TestNG |
| Go | testing package |
| Ruby | RSpec, Minitest |
| C# | xUnit, NUnit, MSTest |
| PHP | PHPUnit |
| Rust | cargo test |

## Example Output

For a JavaScript validation function:

```javascript
// Input: src/utils/validator.js
function validateEmail(email) {
  if (!email) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Generated: src/utils/validator.test.js
describe('validateEmail', () => {
  it('should return true for valid email addresses', () => {
    expect(validateEmail('[email protected]')).toBe(true);
    expect(validateEmail('[email protected]')).toBe(true);
  });

  it('should return false for invalid email addresses', () => {
    expect(validateEmail('notanemail')).toBe(false);
    expect(validateEmail('@example.com')).toBe(false);
    expect(validateEmail('user@')).toBe(false);
  });

  it('should return false for null or undefined inputs', () => {
    expect(validateEmail(null)).toBe(false);
    expect(validateEmail(undefined)).toBe(false);
    expect(validateEmail('')).toBe(false);
  });

  it('should handle edge cases', () => {
    expect(validateEmail('a@b.c')).toBe(true); // Minimal valid email
    expect(validateEmail('user@domain.co.uk')).toBe(true); // Multiple dots
  });
});
```

## Best Practices

The plugin follows testing best practices:

- **Descriptive names** - Clear what is tested and expected result
- **Arrange-Act-Assert** - Clear test structure
- **Test isolation** - No shared state between tests
- **Single responsibility** - One concept per test
- **Mock external dependencies** - Database calls, API requests, etc.
- **Test both paths** - Success and failure scenarios
- **Edge cases** - Boundaries, nulls, empty values

## Requirements

- Claude Code CLI
- Testing framework installed in project (e.g., `npm install --save-dev jest`)

## Tips

1. Review generated tests and adjust for your specific needs
2. Add integration tests for complex workflows
3. Update tests when code changes
4. Aim for high coverage but prioritize meaningful tests
5. Use generated tests as a starting point, not final solution

## License

MIT
