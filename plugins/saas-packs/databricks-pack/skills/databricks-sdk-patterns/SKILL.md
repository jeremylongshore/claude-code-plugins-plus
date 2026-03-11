---
name: databricks-sdk-patterns
description: |
  Apply production-ready Databricks SDK patterns for Python and REST API.
  Use when implementing Databricks integrations, refactoring SDK usage,
  or establishing team coding standards for Databricks.
  Trigger with phrases like "databricks SDK patterns", "databricks best practices",
  "databricks code patterns", "idiomatic databricks".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks SDK Patterns

## Overview
Production-ready patterns for Databricks SDK usage in Python.

## Prerequisites
- Completed `databricks-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern

### Step 2: Add Error Handling Wrapper

### Step 3: Implement Retry Logic with Backoff

### Step 4: Context Manager for Clusters

### Step 5: Type-Safe Job Builders

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Type-safe client singleton
- Robust error handling with structured logging
- Automatic retry with exponential backoff
- Fluent job builder pattern

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Result wrapper | All API calls | Type-safe error handling |
| Retry logic | Transient failures | Improves reliability |
| Context managers | Cluster lifecycle | Resource cleanup |
| Builders | Job creation | Type safety and fluency |

## Resources
- [Databricks SDK for Python](https://docs.databricks.com/dev-tools/sdk-python.html)
- [API Reference](https://docs.databricks.com/api/workspace/introduction)
- [Error Handling](https://docs.databricks.com/dev-tools/sdk-python.html#error-handling)

## Next Steps
Apply patterns in `databricks-core-workflow-a` for Delta Lake ETL.

## Examples

**Basic usage**: Apply databricks sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize databricks sdk patterns for production environments with multiple constraints and team-specific requirements.