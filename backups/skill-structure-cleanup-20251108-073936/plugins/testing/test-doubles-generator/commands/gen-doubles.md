---
description: Generate test doubles (mocks, stubs, spies, fakes) for unit testing
shortcut: gd
---

# Test Doubles Generator

Generate appropriate test doubles (mocks, stubs, spies, fakes, dummies) for unit testing based on the testing framework and dependencies being tested.

## What You Do

1. **Analyze Dependencies**
   - Identify external dependencies in code under test
   - Determine appropriate test double type for each
   - Generate test doubles with proper behavior

2. **Generate Mocks**
   - Create mock implementations with verification
   - Set up method expectations and return values
   - Configure mock behavior for test scenarios

3. **Generate Stubs**
   - Create stub implementations with predefined responses
   - Handle edge cases and error conditions
   - Provide test data fixtures

4. **Generate Spies**
   - Wrap real implementations with call tracking
   - Capture arguments and return values
   - Enable behavior verification

## Usage Pattern

When invoked, you should:

1. Analyze the code file or function to be tested
2. Identify all dependencies (APIs, databases, services, etc.)
3. Recommend appropriate test double type for each dependency
4. Generate test doubles with realistic behavior
5. Provide example test cases using the doubles
6. Include setup and teardown code

## Output Format

```markdown
## Test Doubles Generated for: [Component]

### Dependencies Identified: [N]

#### Dependency: [Name]
**Type:** [API / Database / Service / File System]
**Test Double:** [Mock / Stub / Spy / Fake]
**Rationale:** [Why this type]

**Implementation:**

\`\`\`javascript
// Mock for [Name]
const mock[Name] = {
  methodName: jest.fn()
    .mockResolvedValueOnce([success response])
    .mockRejectedValueOnce(new Error('[error]')),

  anotherMethod: jest.fn().mockReturnValue([value])
};
\`\`\`

**Usage in Tests:**

\`\`\`javascript
describe('[Component]', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should [behavior]', async () => {
    // Arrange
    mock[Name].methodName.mockResolvedValue([data]);

    // Act
    const result = await componentUnderTest.action();

    // Assert
    expect(mock[Name].methodName).toHaveBeenCalledWith([expected args]);
    expect(result).toEqual([expected result]);
  });

  it('should handle errors', async () => {
    // Arrange
    mock[Name].methodName.mockRejectedValue(new Error('[error]'));

    // Act & Assert
    await expect(componentUnderTest.action()).rejects.toThrow('[error]');
  });
});
\`\`\`

### Test Data Fixtures

\`\`\`javascript
const fixtures = {
  validData: { /* ... */ },
  invalidData: { /* ... */ },
  edgeCases: { /* ... */ }
};
\`\`\`

### Next Steps
- [ ] Implement generated test doubles
- [ ] Write test cases using doubles
- [ ] Verify test coverage
- [ ] Refactor for reusability
```

## Test Double Types

**Mock**: Behavior verification, tracks calls and arguments
**Stub**: State verification, returns predefined responses
**Spy**: Wraps real object, tracks interactions
**Fake**: Working implementation with shortcuts (in-memory DB)
**Dummy**: Placeholder objects, not used in test

## Framework Support

- Jest (JavaScript/TypeScript)
- Sinon.js (JavaScript)
- unittest.mock (Python)
- Mockito (Java)
- Moq (.NET)
- RSpec mocks (Ruby)
