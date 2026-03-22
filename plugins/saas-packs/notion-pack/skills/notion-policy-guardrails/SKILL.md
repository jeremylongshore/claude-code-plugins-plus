---
name: notion-policy-guardrails
description: |
  Implement lint rules, CI checks, and runtime guardrails for Notion integrations.
  Use when setting up code quality rules, implementing pre-commit hooks,
  or configuring automated validation for Notion API usage.
  Trigger with phrases like "notion policy", "notion lint",
  "notion guardrails", "notion best practices check", "notion code review".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Policy & Guardrails

## Overview
Automated policy enforcement for Notion integrations: secret scanning, API usage validation, runtime guards, and CI checks.

## Prerequisites
- ESLint or similar linter configured
- CI/CD pipeline (GitHub Actions)
- TypeScript for compile-time checks

## Instructions

### Step 1: Secret Scanning
```bash
#!/bin/bash
# scripts/scan-notion-secrets.sh
echo "Scanning for Notion tokens..."

# Notion internal integration tokens
if grep -rE "(ntn_|secret_)[a-zA-Z0-9]{30,}" \
  --include="*.ts" --include="*.js" --include="*.json" --include="*.yaml" \
  --exclude-dir=node_modules --exclude-dir=.git .; then
  echo "ERROR: Notion token found in source code!"
  echo "Move tokens to environment variables."
  exit 1
fi

# OAuth client secrets
if grep -rE "NOTION_OAUTH_CLIENT_SECRET.*=.*['\"][a-zA-Z0-9]{20,}['\"]" \
  --include="*.ts" --include="*.js" --exclude-dir=node_modules .; then
  echo "ERROR: Notion OAuth secret found in source code!"
  exit 1
fi

echo "OK: No Notion tokens found in source."
```

### Step 2: ESLint Rules for Notion Patterns
```javascript
// eslint-rules/no-notion-secrets.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow hardcoded Notion tokens' },
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value === 'string') {
          if (/^(ntn_|secret_)[a-zA-Z0-9]{30,}/.test(node.value)) {
            context.report({
              node,
              message: 'Hardcoded Notion token detected. Use process.env.NOTION_TOKEN.',
            });
          }
        }
      },
    };
  },
};

// eslint-rules/notion-require-error-handling.js
module.exports = {
  meta: {
    type: 'suggestion',
    docs: { description: 'Require error handling for Notion API calls' },
  },
  create(context) {
    return {
      // Flag notion.X.Y() calls not in try/catch
      CallExpression(node) {
        if (node.callee?.object?.object?.name === 'notion') {
          // Check if inside try block
          let parent = node.parent;
          let inTry = false;
          while (parent) {
            if (parent.type === 'TryStatement') { inTry = true; break; }
            parent = parent.parent;
          }
          if (!inTry) {
            context.report({
              node,
              message: 'Notion API calls should be wrapped in try/catch for error handling.',
            });
          }
        }
      },
    };
  },
};
```

### Step 3: CI Policy Checks
```yaml
# .github/workflows/notion-policy.yml
name: Notion Policy Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for Notion secrets
        run: |
          if grep -rE "(ntn_|secret_)[a-zA-Z0-9]{30,}" \
            --include="*.ts" --include="*.js" --include="*.json" \
            --exclude-dir=node_modules --exclude-dir=.git .; then
            echo "::error::Notion token found in source code"
            exit 1
          fi

      - name: Check .env files not committed
        run: |
          if git ls-files | grep -E "^\.env($|\.local|\.production)"; then
            echo "::error::.env file committed to repository"
            exit 1
          fi

      - name: Verify NOTION_TOKEN from env only
        run: |
          if grep -rn "new Client.*auth:.*['\"]ntn_\|new Client.*auth:.*['\"]secret_" \
            --include="*.ts" --include="*.js" \
            --exclude-dir=node_modules .; then
            echo "::error::Client initialized with hardcoded token"
            exit 1
          fi
```

### Step 4: TypeScript Compile-Time Guards
```typescript
// src/notion/types.ts

// Enforce that properties match expected types
type NotionPropertyType = 'title' | 'rich_text' | 'number' | 'select' |
  'multi_select' | 'date' | 'checkbox' | 'url' | 'email' |
  'phone_number' | 'people' | 'relation' | 'formula' | 'rollup';

// Define your database schema as a type
interface TaskDbSchema {
  Name: 'title';
  Status: 'select';
  Priority: 'select';
  'Due Date': 'date';
  Tags: 'multi_select';
  Assignee: 'people';
  Archived: 'checkbox';
}

// Type-safe property builder
type PropertyValueFor<T extends NotionPropertyType> =
  T extends 'title' ? { title: Array<{ text: { content: string } }> } :
  T extends 'select' ? { select: { name: string } | null } :
  T extends 'multi_select' ? { multi_select: Array<{ name: string }> } :
  T extends 'date' ? { date: { start: string; end?: string } | null } :
  T extends 'number' ? { number: number | null } :
  T extends 'checkbox' ? { checkbox: boolean } :
  T extends 'rich_text' ? { rich_text: Array<{ text: { content: string } }> } :
  T extends 'url' ? { url: string | null } :
  T extends 'email' ? { email: string | null } :
  never;

// Usage: compile-time validation of property types
type TaskProperties = {
  [K in keyof TaskDbSchema]: PropertyValueFor<TaskDbSchema[K]>;
};

// This will give a TypeScript error if you use wrong types:
const taskProps: Partial<TaskProperties> = {
  Name: { title: [{ text: { content: 'My Task' } }] },
  Status: { select: { name: 'Done' } },
  // Status: { number: 42 }, // TypeScript ERROR: not assignable
};
```

### Step 5: Runtime Guards
```typescript
// Prevent dangerous operations in production
const PRODUCTION_BLOCKED_PATTERNS = [
  /delete.*all/i,
  /archive.*all/i,
  /clear.*database/i,
  /reset.*data/i,
];

function guardDangerousOperation(description: string) {
  if (process.env.NODE_ENV === 'production') {
    if (PRODUCTION_BLOCKED_PATTERNS.some(p => p.test(description))) {
      throw new Error(`Operation "${description}" is blocked in production`);
    }
  }
}

// Rate limit self-protection
class SelfRateLimiter {
  private requestTimestamps: number[] = [];
  private readonly windowMs = 1000;
  private readonly maxPerWindow = 3;

  check(): boolean {
    const now = Date.now();
    this.requestTimestamps = this.requestTimestamps.filter(t => t > now - this.windowMs);

    if (this.requestTimestamps.length >= this.maxPerWindow) {
      console.warn('Self-rate-limit: approaching Notion API limit');
      return false;
    }

    this.requestTimestamps.push(now);
    return true;
  }
}

// Startup validation
function validateNotionConfig() {
  const checks = [
    { name: 'NOTION_TOKEN set', pass: !!process.env.NOTION_TOKEN },
    { name: 'Token format valid', pass: /^(ntn_|secret_)/.test(process.env.NOTION_TOKEN ?? '') },
    { name: 'Not a production token in dev', pass: !(process.env.NODE_ENV === 'development' && process.env.NOTION_TOKEN?.includes('prod')) },
  ];

  const failed = checks.filter(c => !c.pass);
  if (failed.length > 0) {
    console.error('Notion config validation failed:');
    failed.forEach(c => console.error(`  FAIL: ${c.name}`));
    throw new Error('Notion configuration invalid');
  }
  console.log('Notion config validation passed');
}
```

### Step 6: Pre-Commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: notion-secrets
        name: Check for Notion tokens
        entry: bash scripts/scan-notion-secrets.sh
        language: system
        pass_filenames: false
```

## Output
- Secret scanning catching tokens before commit
- ESLint rules enforcing Notion best practices
- CI pipeline blocking policy violations
- TypeScript types preventing property mismatches
- Runtime guards protecting production

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| False positive in secret scan | Test fixtures | Add `--exclude` for test files |
| ESLint rule not triggering | Plugin not loaded | Check ESLint config |
| Type errors too strict | Schema changed | Update TypeScript schema types |
| Runtime guard blocking valid operation | Pattern too broad | Narrow regex |

## Examples

### Quick Policy Check
```bash
# One-line secret scan
grep -rn "ntn_\|secret_" --include="*.ts" src/ && echo "FAIL" || echo "PASS"
```

## Resources
- [Notion Best Practices for API Keys](https://developers.notion.com/docs/best-practices-for-handling-api-keys)
- [ESLint Custom Rules](https://eslint.org/docs/latest/extend/plugins)
- [Pre-commit Framework](https://pre-commit.com/)

## Next Steps
For architecture blueprints, see `notion-architecture-variants`.
