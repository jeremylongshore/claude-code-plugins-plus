---
name: cursor-policy-guardrails
description: |
  Implement Cursor lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Cursor integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Cursor best practices.
  Trigger with phrases like "cursor policy", "cursor lint",
  "cursor guardrails", "cursor best practices check", "cursor eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cursor]
---

# Cursor Policy & Guardrails

## Overview
Automated policy enforcement and guardrails for Cursor integrations.

## Prerequisites
- ESLint configured in project
- Pre-commit hooks infrastructure
- CI/CD pipeline with policy checks
- TypeScript for type enforcement

## ESLint Rules

### Custom Cursor Plugin
```javascript
// eslint-plugin-cursor/rules/no-hardcoded-keys.js
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow hardcoded Cursor API keys',
    },
    fixable: 'code',
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value === 'string') {
          if (node.value.match(/^sk_(live|test)_[a-zA-Z0-9]{24,}/)) {
            context.report({
              node,
              message: 'Hardcoded Cursor API key detected',
            });
          }
        }
      },
    };
  },
};
```

### ESLint Configuration
```javascript
// .eslintrc.js
module.exports = {
  plugins: ['cursor'],
  rules: {
    'cursor/no-hardcoded-keys': 'error',
    'cursor/require-error-handling': 'warn',
    'cursor/use-typed-client': 'warn',
  },
};
```

## Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: cursor-secrets-check
        name: Check for Cursor secrets
        entry: bash -c 'git diff --cached --name-only | xargs grep -l "sk_live_" && exit 1 || exit 0'
        language: system
        pass_filenames: false

      - id: cursor-config-validate
        name: Validate Cursor configuration
        entry: node scripts/validate-cursor-config.js
        language: node
        files: '\.cursor\.json$'
```

## TypeScript Strict Patterns

```typescript
// Enforce typed configuration
interface CursorStrictConfig {
  apiKey: string;  // Required
  environment: 'development' | 'staging' | 'production';  // Enum
  timeout: number;  // Required number, not optional
  retries: number;
}

// Disallow any in Cursor code
// @ts-expect-error - Using any is forbidden
const client = new Client({ apiKey: any });

// Prefer this
const client = new CursorClient(config satisfies CursorStrictConfig);
```

## Architecture Decision Records

### ADR Template
```markdown
# ADR-001: Cursor Client Initialization

## Status
Accepted

## Context
We need to decide how to initialize the Cursor client across our application.

## Decision
We will use the singleton pattern with lazy initialization.

## Consequences
- Pro: Single client instance, connection reuse
- Pro: Easy to mock in tests
- Con: Global state requires careful lifecycle management

## Enforcement
- ESLint rule: cursor/use-singleton-client
- CI check: grep for "new CursorClient(" outside allowed files
```

## Policy-as-Code (OPA)

```rego
# cursor-policy.rego
package cursor

# Deny production API keys in non-production environments
deny[msg] {
  input.environment != "production"
  startswith(input.apiKey, "sk_live_")
  msg := "Production API keys not allowed in non-production environment"
}

# Require minimum timeout
deny[msg] {
  input.timeout < 10000
  msg := sprintf("Timeout too low: %d < 10000ms minimum", [input.timeout])
}

# Require retry configuration
deny[msg] {
  not input.retries
  msg := "Retry configuration is required"
}
```

## CI Policy Checks

```yaml
# .github/workflows/cursor-policy.yml
name: Cursor Policy Check

on: [push, pull_request]

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for hardcoded secrets
        run: |
          if grep -rE "sk_(live|test)_[a-zA-Z0-9]{24,}" --include="*.ts" --include="*.js" .; then
            echo "ERROR: Hardcoded Cursor keys found"
            exit 1
          fi

      - name: Validate configuration schema
        run: |
          npx ajv validate -s cursor-config.schema.json -d config/cursor/*.json

      - name: Run ESLint Cursor rules
        run: npx eslint --plugin cursor --rule 'cursor/no-hardcoded-keys: error' src/
```

## Runtime Guardrails

```typescript
// Prevent dangerous operations in production
const BLOCKED_IN_PROD = ['deleteAll', 'resetData', 'migrateDown'];

function guardCursorOperation(operation: string): void {
  const isProd = process.env.NODE_ENV === 'production';

  if (isProd && BLOCKED_IN_PROD.includes(operation)) {
    throw new Error(`Operation '${operation}' blocked in production`);
  }
}

// Rate limit protection
function guardRateLimits(requestsInWindow: number): void {
  const limit = parseInt(process.env.CURSOR_RATE_LIMIT || '100');

  if (requestsInWindow > limit * 0.9) {
    console.warn('Approaching Cursor rate limit');
  }

  if (requestsInWindow >= limit) {
    throw new Error('Cursor rate limit exceeded - request blocked');
  }
}
```

## Instructions

### Step 1: Create ESLint Rules
Implement custom lint rules for Cursor patterns.

### Step 2: Configure Pre-Commit Hooks
Set up hooks to catch issues before commit.

### Step 3: Add CI Policy Checks
Implement policy-as-code in CI pipeline.

### Step 4: Enable Runtime Guardrails
Add production safeguards for dangerous operations.

## Output
- ESLint plugin with Cursor rules
- Pre-commit hooks blocking secrets
- CI policy checks passing
- Runtime guardrails active

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| ESLint rule not firing | Wrong config | Check plugin registration |
| Pre-commit skipped | --no-verify | Enforce in CI |
| Policy false positive | Regex too broad | Narrow pattern match |
| Guardrail triggered | Actual issue | Fix or whitelist |

## Examples

### Quick ESLint Check
```bash
npx eslint --plugin cursor --rule 'cursor/no-hardcoded-keys: error' src/
```

## Resources
- [ESLint Plugin Development](https://eslint.org/docs/latest/extend/plugins)
- [Pre-commit Framework](https://pre-commit.com/)
- [Open Policy Agent](https://www.openpolicyagent.org/)

## Next Steps
For architecture blueprints, see `cursor-architecture-variants`.