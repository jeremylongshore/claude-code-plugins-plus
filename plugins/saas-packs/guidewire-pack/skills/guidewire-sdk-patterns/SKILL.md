---
name: guidewire-sdk-patterns
description: |
  Master Guidewire SDK patterns including Digital SDK, REST API Client, and Gosu best practices.
  Use when implementing integrations, building frontends with Jutro, or writing server-side Gosu code.
  Trigger with phrases like "guidewire sdk", "digital sdk", "jutro sdk",
  "guidewire patterns", "gosu best practices", "rest api client".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire SDK Patterns

## Overview

Master the key SDK patterns for Guidewire development: Digital SDK for frontends, REST API Client for integrations, and Gosu patterns for server-side development.

## Prerequisites

- Completed `guidewire-install-auth` and `guidewire-hello-world`
- Understanding of TypeScript/JavaScript (for Digital SDK)
- Familiarity with Gosu basics (for server-side patterns)

## Instructions

### Step 1: Digital SDK (Frontend)

Generate the SDK from your Cloud API using `jutro-cli generate-sdk`. Configure with OAuth2 auth, then use generated hooks (`useAccount`, `useAccounts`, `createAccount`) for type-safe CRUD operations. Combine with `zodResolver` for form validation.

### Step 2: REST API Client (Integration)

Configure the Gradle REST API Client plugin with an OpenAPI spec. The generated Gosu client includes automatic retry and circuit breaker. For custom integrations, use `RestClientBuilder` with proper timeout and auth headers.

### Step 3: Gosu Query Patterns

Use `Query.make()` with `compare()` for simple lookups, `join()` for related entities, and `subselect()` for complex filtering. Process large result sets with batch iterators to avoid memory issues.

### Step 4: Transaction Patterns

Always use `GWTransaction.runWithNewBundle()`. Add external entities to the bundle with `bundle.add()` before modifying. Use `AsyncProcess.schedule()` for long-running operations.

### Step 5: Plugin Patterns

Implement `IRatingPlugin` or similar interfaces. Compose calculations from base premium, discounts, and taxes. Log entry points for debugging.

For detailed code implementations (Digital SDK components, Gosu classes, Gradle config), load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Configured Digital SDK with type-safe API calls
- REST API Client with fault tolerance
- Gosu patterns following Guidewire best practices

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| SDK generation failed | Invalid API spec | Verify OpenAPI spec URL and access |
| Type mismatch | Schema changed | Regenerate SDK |
| Transaction timeout | Long-running operation | Optimize or use async |
| Client timeout | Network issues | Increase timeout, add retry |

## Resources

- [Digital SDK Documentation](https://docs.guidewire.com/jutro/documentation/10.12/working-with-cloud-apis/)
- [REST API Client Guide](https://developer.guidewire.com/rest-api-client/)
- [Gosu Language Reference](https://gosu-lang.github.io/)
- [Query API Documentation](https://docs.guidewire.com/cloud/pc/202503/cloudapica/)

## Next Steps

For core insurance workflows, see `guidewire-core-workflow-a` and `guidewire-core-workflow-b`.

## Examples

**Basic usage**: Apply guidewire sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire sdk patterns for production environments with multiple constraints and team-specific requirements.