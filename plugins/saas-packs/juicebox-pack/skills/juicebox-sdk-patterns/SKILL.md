---
name: juicebox-sdk-patterns
description: |
  Apply production-ready Juicebox SDK patterns.
  Use when implementing robust error handling, retry logic,
  or enterprise-grade Juicebox integrations.
  Trigger with phrases like "juicebox best practices", "juicebox patterns",
  "production juicebox", "juicebox SDK architecture".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox SDK Patterns

## Overview
Production-ready patterns for robust Juicebox integration including error handling, retries, and caching.

## Prerequisites
- Juicebox SDK installed
- Understanding of async/await patterns
- Familiarity with dependency injection

## Instructions
- Step 1: Create Client Wrapper
- Step 2: Implement Retry Logic
- Step 3: Add Observability

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Production-ready client wrapper
- Retry logic with exponential backoff
- Caching layer for performance
- Observability instrumentation

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Circuit Breaker | Prevent cascade failures | System resilience |
| Retry with Backoff | Transient errors | Higher success rate |
| Cache-Aside | Repeated queries | Lower latency |
| Bulkhead | Resource isolation | Fault isolation |

## Resources
- [SDK Best Practices](https://juicebox.ai/docs/best-practices)
- [Error Handling Guide](https://juicebox.ai/docs/errors)

## Next Steps
Apply these patterns then explore `juicebox-core-workflow-a` for search workflows.
