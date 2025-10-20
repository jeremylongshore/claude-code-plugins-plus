# Test Doubles Generator

Generate mocks, stubs, spies, and fakes for unit testing with Jest, Sinon, and test frameworks.

## Installation

```bash
/plugin install test-doubles-generator@claude-code-plugins-plus
```

## Usage

```bash
/gen-doubles
# or shortcut
/gd
```

## Features

- **Smart Analysis**: Identifies dependencies and recommends appropriate test double type
- **Multi-Framework**: Jest, Sinon, unittest.mock, Mockito, Moq, RSpec
- **Complete Examples**: Includes test cases demonstrating usage
- **Test Fixtures**: Generate realistic test data
- **Best Practices**: Follows testing framework conventions

## Example Workflow

```bash
# Generate test doubles for a component
/gen-doubles

# Claude analyzes dependencies and generates:
#  Mock implementations for APIs
#  Stub implementations for services
#  Spy wrappers for real objects
#  Test fixtures and example tests
```

## Test Double Types

- **Mock**: Behavior verification with call tracking
- **Stub**: Predefined responses for dependencies
- **Spy**: Wrap real implementations with tracking
- **Fake**: Working simplified implementations
- **Dummy**: Placeholder objects

## Files

- `commands/gen-doubles.md` - Test doubles generation command

## License

MIT
