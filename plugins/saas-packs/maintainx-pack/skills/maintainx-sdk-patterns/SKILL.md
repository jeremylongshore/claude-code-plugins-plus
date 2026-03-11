---
name: maintainx-sdk-patterns
description: |
  Learn MaintainX REST API patterns, pagination, filtering, and client architecture.
  Use when building robust API integrations, implementing pagination,
  or creating reusable SDK patterns for MaintainX.
  Trigger with phrases like "maintainx sdk", "maintainx api patterns",
  "maintainx pagination", "maintainx filtering", "maintainx client design".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX SDK Patterns

## Overview
Production-grade patterns for building robust MaintainX API integrations with proper error handling, pagination, and type safety.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Understanding of REST API principles
- TypeScript/Node.js familiarity

## Instructions
Follow these high-level steps to implement maintainx-sdk-patterns:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-sdk-patterns/references/implementation-guide.md)`

## Output
- Type-safe MaintainX client with full TypeScript support
- Cursor-based pagination utilities
- Retry logic with exponential backoff
- Batch processing helpers
- Fluent query builder

## Error Handling
| Pattern | Use Case |
|---------|----------|
| Retry with backoff | Transient errors (429, 5xx) |
| Pagination | Large result sets |
| Batch processing | Bulk operations |
| Query builder | Complex filtering |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [REST API Best Practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)

## Next Steps
For core workflows, see `maintainx-core-workflow-a` (Work Orders) and `maintainx-core-workflow-b` (Assets).
