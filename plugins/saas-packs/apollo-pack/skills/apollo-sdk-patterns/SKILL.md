---
name: apollo-sdk-patterns
description: |
  Apply production-ready Apollo.io SDK patterns.
  Use when implementing Apollo integrations, refactoring API usage,
  or establishing team coding standards.
  Trigger with phrases like "apollo sdk patterns", "apollo best practices",
  "apollo code patterns", "idiomatic apollo", "apollo client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo SDK Patterns

## Overview
Production-ready patterns for Apollo.io API integration with type safety, error handling, and retry logic.

## Prerequisites
- Completed `apollo-install-auth` setup
- Familiarity with async/await patterns
- Understanding of TypeScript generics

## Instructions
Follow these high-level steps to implement apollo-sdk-patterns:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-sdk-patterns/references/implementation-guide.md)`

## Output
- Type-safe client singleton with Zod validation
- Robust error handling with custom error classes
- Automatic retry with exponential backoff
- Async pagination iterator
- Request batching for bulk operations

## Error Handling
| Pattern | When to Use |
|---------|-------------|
| Singleton | Always - ensures single client instance |
| Retry | Network errors, 429/500 responses |
| Pagination | Large result sets (>100 records) |
| Batching | Multiple enrichment calls |
| Custom Errors | Distinguish error types in catch blocks |

## Resources
- [Zod Documentation](https://zod.dev/)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)
- [TypeScript Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)

## Next Steps
Proceed to `apollo-core-workflow-a` for lead search implementation.

## Examples

**Basic usage**: Apply apollo sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo sdk patterns for production environments with multiple constraints and team-specific requirements.