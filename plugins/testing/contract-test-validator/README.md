# Contract Test Validator

API contract testing with Pact, OpenAPI validation, and consumer-driven contract verification.

## Installation

```bash
/plugin install contract-test-validator@claude-code-plugins-plus
```

## Usage

```bash
/contract-test
# or shortcut
/ct
```

## Features

- **Consumer-Driven Testing**: Generate and verify Pact contracts
- **OpenAPI Validation**: Validate APIs against OpenAPI specs
- **Breaking Change Detection**: Identify incompatible API changes
- **Multi-Protocol**: REST, GraphQL, gRPC support
- **CI/CD Integration**: Automated contract verification
- **Contract Evolution**: Version management and migration strategies

## Example Workflow

```bash
# Generate contract tests for your API
/contract-test

# Claude analyzes your API and generates:
#  Pact consumer contracts
#  Provider verification tests
#  OpenAPI validation
#  Breaking change detection
```

## Supported Technologies

- Pact (Consumer-Driven Contracts)
- OpenAPI 3.x
- GraphQL schemas
- gRPC/Protobuf
- JSON Schema
- Spring Cloud Contract

## Files

- `commands/contract-test.md` - Main contract testing command

## License

MIT
