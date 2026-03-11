---
name: linear-sdk-patterns
description: |
  TypeScript/JavaScript SDK patterns and best practices for Linear.
  Use when learning SDK idioms, implementing common patterns,
  or optimizing Linear API usage.
  Trigger with phrases like "linear SDK patterns", "linear best practices",
  "linear typescript", "linear API patterns", "linear SDK idioms".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear SDK Patterns

## Overview
Essential patterns and best practices for working with the Linear SDK.

## Prerequisites
- Linear SDK installed and configured
- TypeScript project setup
- Understanding of async/await patterns

## Instructions
- Core Patterns

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Reusable client singleton
- Pagination iterator for large datasets
- Type-safe error handling
- Efficient batch operations
- Caching for performance

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Type mismatch` | SDK version incompatibility | Update @linear/sdk package |
| `Undefined property` | Nullable field access | Use optional chaining (?.) |
| `Promise rejection` | Unhandled async error | Wrap in try/catch or use wrapper |

## Resources
- [Linear SDK TypeScript](https://developers.linear.app/docs/sdk/getting-started)
- [GraphQL Schema Reference](https://developers.linear.app/docs/graphql/schema)
- [TypeScript Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)

## Next Steps
Apply these patterns in `linear-core-workflow-a` for issue management.
