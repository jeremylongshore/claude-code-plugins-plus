---
name: documenso-sdk-patterns
description: |
  Apply production-ready Documenso SDK patterns for TypeScript and Python.
  Use when implementing Documenso integrations, refactoring SDK usage,
  or establishing team coding standards for Documenso.
  Trigger with phrases like "documenso SDK patterns", "documenso best practices",
  "documenso code patterns", "idiomatic documenso".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso SDK Patterns

## Overview
Production-ready patterns for Documenso SDK usage in TypeScript and Python.

## Prerequisites
- Completed `documenso-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Instructions
// src/documenso/client.ts

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output


- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [Python implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling
| Issue | Solution |
|-------|----------|
| Configuration error | Check settings |

## Resources
- [Documenso SDK Documentation](https://github.com/documenso/sdk-typescript)
- [Zod Documentation](https://zod.dev/)
- [Error Handling Best Practices](https://docs.documenso.com/developers)

## Next Steps
Apply patterns in `documenso-core-workflow-a` for document creation workflows.

## Examples

**Basic usage**: Apply documenso sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso sdk patterns for production environments with multiple constraints and team-specific requirements.