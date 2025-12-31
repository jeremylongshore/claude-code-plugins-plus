# vercel-sdk-patterns

## Skill Scaffold

```
vercel-sdk-patterns/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Apply production-ready Vercel SDK patterns including singleton client, error handling, retry logic, and Zod validation.
**Workflow:** Reference during code development and code review to ensure patterns meet production standards.
**Relates to:** Builds on vercel-local-dev-loop; patterns are used in vercel-deploy-preview and vercel-edge-functions

## Summary

This skill provides battle-tested patterns for Vercel SDK usage in TypeScript and Python. It covers singleton client instantiation to avoid connection overhead, safe wrapper functions for error handling, exponential backoff with retry logic for transient failures, and factory patterns for multi-tenant scenarios. These patterns form the foundation for all production Vercel code.
