---
name: lindy-sdk-patterns
description: |
  Lindy AI SDK best practices and common patterns.
  Use when learning SDK patterns, optimizing API usage,
  or implementing advanced agent features.
  Trigger with phrases like "lindy SDK patterns", "lindy best practices",
  "lindy API patterns", "lindy code patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy SDK Patterns

## Overview
Essential SDK patterns and best practices for Lindy AI agent development.

## Prerequisites
- Completed `lindy-install-auth` setup
- Basic understanding of async/await
- Familiarity with TypeScript

## Instructions

### Pattern 1: Client Singleton
### Pattern 2: Agent Factory
### Pattern 3: Retry with Backoff
### Pattern 4: Streaming Responses

1. For detailed implementation code and configurations, load the reference guide:
2. `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Reusable client singleton pattern
- Agent factory for consistent creation
- Robust error handling with retries
- Streaming support for real-time output

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | Connection reuse | Reduced overhead |
| Factory | Agent creation | Consistency |
| Retry | Rate limits | Reliability |
| Streaming | Long responses | Better UX |

## Examples

### Complete Agent Service
## Resources
- [Lindy SDK Patterns](https://docs.lindy.ai/patterns)
- [TypeScript Best Practices](https://docs.lindy.ai/typescript)

## Next Steps
Proceed to `lindy-core-workflow-a` for agent creation workflows.