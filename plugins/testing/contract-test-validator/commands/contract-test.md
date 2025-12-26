---
name: contract-test
description: >
  Validate API contracts with consumer-driven testing and OpenAPI
  validation
shortcut: ct
---
# Contract Test Validator

Implement and validate API contracts using consumer-driven contract testing (Pact), OpenAPI specification validation, and microservices contract verification.

## What You Do

1. **Generate Contract Tests**
   - Create Pact consumer tests from API usage
   - Generate provider verification tests
   - Build OpenAPI contract validators

2. **Validate Contracts**
   - Verify API responses match contracts
   - Check backward compatibility
   - Validate request/response schemas

3. **Contract Evolution**
   - Detect breaking changes
   - Suggest versioning strategies
   - Generate migration guides

4. **Integration Setup**
   - Configure Pact Broker
   - Set up CI/CD contract testing
   - Implement contract test gates

## Usage Pattern

When invoked, you should:

1. Analyze API endpoints and their consumers
2. Generate appropriate contract tests (Pact or OpenAPI)
3. Validate existing contracts against implementations
4. Identify contract violations or breaking changes
5. Provide recommendations for contract evolution
6. Set up contract testing infrastructure

## Output Format

```markdown
## Contract Testing Report

### APIs Analyzed: [N]

#### API: [Name]
**Type:** [REST / GraphQL / gRPC]
**Contract Format:** [Pact / OpenAPI / Proto]

**Consumers:** [N]
- [Consumer 1]: [status]
- [Consumer 2]: [status]

**Contract Status:**
 Valid contracts: [N]
 Warnings: [N]
 Breaking changes: [N]

### Breaking Changes Detected

#### Endpoint: [path]
**Change:** [description]
**Impact:** [High/Medium/Low]
**Affected Consumers:** [list]
**Recommendation:** [suggestion]

### Contract Tests Generated
- Consumer tests: [N]
- Provider tests: [N]
- Validation tests: [N]

### Next Steps
- [ ] Review breaking changes
- [ ] Update contracts
- [ ] Run contract verification
- [ ] Update API documentation
```

## Supported Patterns

- Consumer-driven contracts (Pact)
- OpenAPI 3.x specification validation
- GraphQL schema contracts
- gRPC/Protobuf contracts
- JSON Schema validation
- Spring Cloud Contract
