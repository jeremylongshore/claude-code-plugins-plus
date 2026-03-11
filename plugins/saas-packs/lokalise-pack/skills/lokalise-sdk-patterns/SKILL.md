---
name: lokalise-sdk-patterns
description: |
  Apply production-ready Lokalise SDK patterns for TypeScript and Node.js.
  Use when implementing Lokalise integrations, refactoring SDK usage,
  or establishing team coding standards for Lokalise.
  Trigger with phrases like "lokalise SDK patterns", "lokalise best practices",
  "lokalise code patterns", "idiomatic lokalise".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise SDK Patterns

## Overview
Production-ready patterns for Lokalise SDK usage in TypeScript and Node.js applications.

## Prerequisites
- Completed `lokalise-install-auth` setup
- Familiarity with async/await and TypeScript
- Understanding of error handling best practices

## Instructions

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Type-safe client singleton with compression
- Robust error handling with retryable detection
- Rate-limited request queue
- Automatic retry with exponential backoff
- Cursor pagination for large datasets

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Safe wrapper | All API calls | Prevents uncaught exceptions |
| Request queue | Bulk operations | Respects rate limits |
| Retry logic | Transient failures | Improves reliability |
| Pagination | Large datasets | Memory efficient |

## Examples
### Branch-Aware Client
```typescript
export function getProjectWithBranch(projectId: string, branch?: string): string {
  // Lokalise branch syntax: projectId:branchName
  return branch ? `${projectId}:${branch}` : projectId;
}

// Usage
const projectId = getProjectWithBranch("123456.abcdef", "feature/new-ui");
const keys = await client.keys().list({ project_id: projectId });
```

## Resources
- [Node SDK Documentation](https://lokalise.github.io/node-lokalise-api/)
- [Pagination Guide](https://lokalise.github.io/node-lokalise-api/api/getting-started.html)
- [API Error Codes](https://developers.lokalise.com/reference/api-errors)

## Next Steps
Apply patterns in `lokalise-core-workflow-a` for real-world usage.
