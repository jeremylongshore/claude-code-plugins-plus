---
name: windsurf-performance-tuning
description: |
  Optimize Windsurf API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Windsurf integrations.
  Trigger with phrases like "windsurf performance", "optimize windsurf",
  "windsurf latency", "windsurf caching", "windsurf slow", "windsurf batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Windsurf Performance Tuning

## Overview
Optimize Windsurf (Codeium) AI-assisted development workflows. Focus on Cascade flow configuration, context window management, workspace indexing performance, and efficient use of AI completions to minimize latency.

## Prerequisites
- Windsurf IDE installed
- Understanding of Cascade AI flows
- Workspace with codebase indexed
- Familiarity with Windsurf settings

## Instructions

### Step 1: Optimize Workspace Indexing
```json
// .windsurf/settings.json - Exclude large directories from indexing
{
  "codeium.indexing.excludePatterns": [
    "node_modules/**",
    "dist/**",
    "build/**",
    ".git/**",
    "*.min.js",
    "**/*.map",
    "coverage/**",
    "vendor/**",
    ".next/**"
  ],
  "codeium.indexing.maxFileSize": 1048576,
  "codeium.indexing.enableSemanticIndexing": true
}
```

### Step 2: Configure Cascade Flow for Speed
```json
// .windsurf/cascade.json - Tune Cascade behavior
{
  "cascade.contextWindow": {
    "maxFiles": 10,
    "maxTokensPerFile": 2000,
    "preferOpenFiles": true,
    "includeImports": true
  },
  "cascade.suggestions": {
    "debounceMs": 150,
    "maxSuggestions": 3,
    "inlineSuggestionsEnabled": true,
    "multiLineSuggestionsEnabled": true
  },
  "cascade.flows": {
    "preferStreaming": true,
    "timeoutMs": 30000,
    "retryCount": 2
  }
}
```

### Step 3: Efficient Context Management
```typescript
// .windsurf/context.ts - Define project-specific context rules
// Place in workspace root to help Cascade understand your project

/**
 * @windsurf-context
 * Framework: Next.js 14 with App Router
 * Language: TypeScript strict mode
 * Styling: Tailwind CSS
 * State: Zustand
 * Testing: Vitest + Testing Library
 *
 * Key patterns:
 * - Server Components by default
 * - Client Components marked with 'use client'
 * - API routes in app/api/
 * - Shared types in types/
 */

// Create a .windsurfrules file for persistent context
const WINDSURF_RULES = `
When generating code:
- Use TypeScript strict mode
- Prefer async/await over .then()
- Use named exports, not default
- Add JSDoc comments for public APIs
- Use Tailwind classes, not inline styles
`;
```

### Step 4: Keybinding Optimization for Flow Speed
```json
// keybindings.json - Fast access to Cascade features
[
  {
    "key": "ctrl+shift+k",
    "command": "cascade.openChat",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+i",
    "command": "cascade.inlineEdit",
    "when": "editorTextFocus"
  },
  {
    "key": "tab",
    "command": "cascade.acceptSuggestion",
    "when": "cascade.suggestionsVisible"
  },
  {
    "key": "alt+]",
    "command": "cascade.nextSuggestion",
    "when": "cascade.suggestionsVisible"
  }
]
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow indexing | Large node_modules indexed | Add to exclude patterns |
| Irrelevant suggestions | Too much context | Reduce maxFiles and maxTokensPerFile |
| Cascade timeout | Complex multi-file operation | Break into smaller Cascade steps |
| High memory usage | Semantic indexing on large repo | Limit maxFileSize, exclude binaries |

## Examples

### Project-Specific Rules File
```markdown
<!-- .windsurfrules -->
# Project Context for AI

## Architecture
- Monorepo with pnpm workspaces
- packages/api - Express REST API
- packages/web - Next.js frontend
- packages/shared - Shared types

## Conventions
- Use zod for runtime validation
- Error responses follow RFC 7807
- All dates are ISO 8601 UTC
```

## Resources
- [Windsurf Documentation](https://docs.windsurf.com)
- [Cascade AI Guide](https://docs.windsurf.com/cascade)
- [Codeium Configuration](https://codeium.com/documentation)
