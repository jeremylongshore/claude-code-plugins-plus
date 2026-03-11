---
name: validating-api-contracts
description: |
  Validate API contracts using consumer-driven contract testing (Pact, Spring Cloud Contract).
  Use when performing specialized testing.
  Trigger with phrases like "validate API contract", "run contract tests", or "check consumer contracts".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:contract-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Contract Test Validator

## Overview

Validate API contracts between services using consumer-driven contract testing to prevent breaking changes in microservice architectures. Supports Pact (the industry standard for CDC testing), Spring Cloud Contract (JVM), and OpenAPI-diff for specification comparison. Ensures that providers honor the expectations of all consumers and that schema changes are backward-compatible before deployment.

## Prerequisites

- Contract testing framework installed (Pact JS/Python/JVM, or Spring Cloud Contract)
- Pact Broker running (or PactFlow SaaS) for contract storage and verification
- Consumer and provider services with clearly defined API boundaries
- Existing integration points documented (which consumers call which provider endpoints)
- CI pipeline configured for both consumer and provider repositories

## Instructions

1. Identify consumer-provider relationships in the system:
   - Map which services call which APIs (e.g., Frontend calls User API, Order API calls Payment API).
   - Document each interaction: HTTP method, path, headers, request body, expected response.
   - Prioritize contracts for the most critical and frequently changing integrations.
2. Write consumer-side contract tests (Pact consumer tests):
   - Define the expected interaction: method, path, query parameters, headers, request body.
   - Specify the expected response: status code, headers, and response body structure.
   - Use matchers for flexible assertions (`like()`, `eachLike()`, `term()`) instead of exact values.
   - Generate a Pact file (JSON contract) from the consumer test.
3. Publish consumer contracts to the Pact Broker:
   - Run `pact-broker publish` with the consumer version and branch/tag.
   - Enable webhooks to trigger provider verification when new contracts are published.
   - Configure can-i-deploy checks in CI to gate deployments.
4. Write provider-side verification tests:
   - Configure the Pact verifier to fetch contracts from the Pact Broker.
   - Set up provider states (test data scenarios matching consumer expectations).
   - Run verification against the actual provider implementation.
   - Publish verification results back to the Pact Broker.
5. Handle contract evolution:
   - Adding new fields: Safe -- consumers using matchers will not break.
   - Removing fields: Breaking -- coordinate with all consumers before removal.
   - Changing field types: Breaking -- requires consumer updates first.
   - Use `can-i-deploy` to check compatibility before releasing either side.
6. For schema-based validation (non-Pact):
   - Compare OpenAPI spec versions using `openapi-diff` to detect breaking changes.
   - Flag removed endpoints, changed parameter types, and narrowed response schemas.
   - Run schema validation tests against the actual API responses.
7. Integrate contract tests into the CI/CD pipeline for both consumers and providers.

## Output

- Consumer Pact test files defining expected API interactions
- Generated Pact contract files (JSON) in `pacts/` directory
- Provider verification test configuration
- Pact Broker deployment with published contracts and verification status
- CI pipeline integration with `can-i-deploy` deployment gates
- Contract evolution report flagging breaking vs. non-breaking changes

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Provider verification fails | Provider response does not match consumer expectations | Check if the contract is outdated; update consumer tests if the change is intentional; fix provider if regression |
| `can-i-deploy` blocks release | Consumer has unverified or failed contracts | Run provider verification; check if the right version tags are published; verify Pact Broker webhook fired |
| Pact Broker connection error | Broker URL or credentials misconfigured | Verify `PACT_BROKER_BASE_URL` and `PACT_BROKER_TOKEN` environment variables; check network connectivity |
| Provider state not found | Consumer test references a state the provider does not implement | Add the missing provider state setup function; align state names between consumer and provider |
| Too many contracts to maintain | Every consumer-provider pair has extensive contracts | Focus on critical interactions; use matchers instead of exact values; consolidate similar interactions |

## Examples

**Pact consumer test (JavaScript):**
```typescript
import { PactV4 } from '@pact-foundation/pact';

const provider = new PactV4({ consumer: 'Frontend', provider: 'UserAPI' });

describe('User API Contract', () => {
  it('fetches a user by ID', async () => {
    await provider
      .addInteraction()
      .given('user with ID 1 exists')
      .uponReceiving('a request for user 1')
      .withRequest('GET', '/api/users/1', (builder) => {
        builder.headers({ Accept: 'application/json' });
      })
      .willRespondWith(200, (builder) => {
        builder
          .headers({ 'Content-Type': 'application/json' })
          .jsonBody({
            id: like('1'),
            name: like('Alice'),
            email: like('alice@example.com'),
          });
      })
      .executeTest(async (mockServer) => {
        const response = await fetch(`${mockServer.url}/api/users/1`);
        const user = await response.json();
        expect(user.name).toBeDefined();
      });
  });
});
```

**Provider verification test:**
```typescript
import { Verifier } from '@pact-foundation/pact';

describe('User API Provider Verification', () => {
  it('validates consumer contracts', async () => {
    await new Verifier({
      providerBaseUrl: 'http://localhost:3000',
      pactBrokerUrl: process.env.PACT_BROKER_BASE_URL,
      pactBrokerToken: process.env.PACT_BROKER_TOKEN,
      provider: 'UserAPI',
      publishVerificationResult: true,
      providerVersion: process.env.GIT_SHA,
      stateHandlers: {
        'user with ID 1 exists': async () => {
          await db.users.create({ id: '1', name: 'Alice', email: 'alice@example.com' });
        },
      },
    }).verifyProvider();
  });
});
```

**can-i-deploy CI check:**
```bash
pact-broker can-i-deploy \
  --pacticipant Frontend \
  --version $(git rev-parse HEAD) \
  --to-environment production \
  --broker-base-url $PACT_BROKER_URL \
  --broker-token $PACT_BROKER_TOKEN
```

## Resources

- Pact documentation: https://docs.pact.io/
- PactFlow (managed Pact Broker): https://pactflow.io/
- Spring Cloud Contract: https://spring.io/projects/spring-cloud-contract
- openapi-diff: https://github.com/OpenAPITools/openapi-diff
- Consumer-Driven Contracts: https://martinfowler.com/articles/consumerDrivenContracts.html
