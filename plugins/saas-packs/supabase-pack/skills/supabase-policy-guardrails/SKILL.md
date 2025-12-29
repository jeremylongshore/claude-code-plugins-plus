---
name: supabase-policy-guardrails
description: |
  Supabase lint rules, policy enforcement, and guardrails.
  Use when implementing policy enforcement for Supabase integration.
  Trigger with phrases like "supabase policy", "supabase lint",
  "supabase guardrails", "supabase best practices check".
allowed-tools: Read, Write, Edit, Bash(supabase:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Policy & Guardrails

## Overview
Automated policy enforcement and guardrails for Supabase integrations.

## Prerequisites
- supabase-install-auth completed
- ESLint configured in project
- CI/CD pipeline available
- Pre-commit hooks installed

## Instructions

### Step 1: ESLint Rules

### Custom Supabase Plugin
```javascript
// eslint-plugin-supabase/rules/no-hardcoded-keys.js
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow hardcoded Supabase API keys',
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
              message: 'Hardcoded Supabase API key detected',
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
  plugins: ['supabase'],
  rules: {
    'supabase/no-hardcoded-keys': 'error',
    'supabase/require-error-handling': 'warn',
    'supabase/use-typed-client': 'warn',
  },
};
```

## Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: supabase-secrets-check
        name: Check for Supabase secrets
        entry: bash -c 'git diff --cached --name-only | xargs grep -l "sk_live_" && exit 1 || exit 0'
        language: system
        pass_filenames: false

      - id: supabase-config-validate
        name: Validate Supabase configuration
        entry: node scripts/validate-supabase-config.js
        language: node
        files: '\.supabase\.json$'
```

## TypeScript Strict Patterns

```typescript
// Enforce typed configuration
interface SupabaseStrictConfig {
  apiKey: string;  // Required
  environment: 'development' | 'staging' | 'production';  // Enum
  timeout: number;  // Required number, not optional
  retries: number;
}

// Disallow any in Supabase code
// @ts-expect-error - Using any is forbidden
const client = new Client({ apiKey: any });

// Prefer this
const client = new SupabaseClient(config satisfies SupabaseStrictConfig);
```

## Architecture Decision Records

### ADR Template
```markdown
# ADR-001: Supabase Client Initialization

## Status
Accepted

## Context
We need to decide how to initialize the Supabase client across our application.

## Decision
We will use the singleton pattern with lazy initialization.

## Consequences
- Pro: Single client instance, connection reuse
- Pro: Easy to mock in tests
- Con: Global state requires careful lifecycle management

## Enforcement
- ESLint rule: supabase/use-singleton-client
- CI check: grep for "new SupabaseClient(" outside allowed files
```

## Policy-as-Code (OPA)

```rego
# supabase-policy.rego
package supabase

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
# .github/workflows/supabase-policy.yml
name: Supabase Policy Check

on: [push, pull_request]

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for hardcoded secrets
        run: |
          if grep -rE "sk_(live|test)_[a-zA-Z0-9]{24,}" --include="*.ts" --include="*.js" .; then
            echo "ERROR: Hardcoded Supabase keys found"
            exit 1
          fi

      - name: Validate configuration schema
        run: |
          npx ajv validate -s supabase-config.schema.json -d config/supabase/*.json

      - name: Run ESLint Supabase rules
        run: npx eslint --plugin supabase --rule 'supabase/no-hardcoded-keys: error' src/
```

### Step 2: Runtime Guardrails

```typescript
// Prevent dangerous operations in production
const BLOCKED_IN_PROD = ['deleteAll', 'resetData', 'migrateDown'];

function guardSupabaseOperation(operation: string): void {
  const isProd = process.env.NODE_ENV === 'production';

  if (isProd && BLOCKED_IN_PROD.includes(operation)) {
    throw new Error(`Operation '${operation}' blocked in production`);
  }
}

// Rate limit protection
function guardRateLimits(requestsInWindow: number): void {
  const limit = parseInt(process.env.SUPABASE_RATE_LIMIT || '100');

  if (requestsInWindow > limit * 0.9) {
    console.warn('Approaching Supabase rate limit');
  }

  if (requestsInWindow >= limit) {
    throw new Error('Supabase rate limit exceeded - request blocked');
  }
}
```

## Output
- ESLint rules catching Supabase anti-patterns
- Pre-commit hooks blocking secrets
- CI policy checks in every PR
- Runtime guardrails preventing dangerous operations

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| ESLint rule violation | Code anti-pattern | Fix code or disable rule with comment |
| Pre-commit rejection | Secret detected | Remove secret, use environment variable |
| OPA policy denial | Configuration violation | Update config to comply with policy |
| Runtime guard block | Dangerous operation in prod | Use appropriate environment or override |

## Examples

### Semgrep Rules

```yaml
rules:
  - id: supabase-hardcoded-key
    pattern: |
      new $CLIENT({ apiKey: "sk_..." })
    message: Hardcoded Supabase API key detected
    severity: ERROR
    languages: [typescript, javascript]
```

### Complete ESLint Plugin Setup

```javascript
// eslint-plugin-supabase/index.js
module.exports = {
  rules: {
    'no-hardcoded-keys': require('./rules/no-hardcoded-keys'),
    'require-error-handling': require('./rules/require-error-handling'),
    'use-typed-client': require('./rules/use-typed-client'),
  },
  configs: {
    recommended: {
      plugins: ['supabase'],
      rules: {
        'supabase/no-hardcoded-keys': 'error',
        'supabase/require-error-handling': 'warn',
        'supabase/use-typed-client': 'warn',
      },
    },
  },
};
```

### Git Hooks Configuration

```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Running Supabase policy checks..."

# Check for secrets
if grep -rE "sk_(live|test)_[a-zA-Z0-9]{24,}" --include="*.ts" --include="*.js" .; then
  echo "ERROR: Supabase secrets detected!"
  exit 1
fi

# Run ESLint
npx eslint --plugin supabase --rule 'supabase/no-hardcoded-keys: error' src/

echo "Supabase policy checks passed!"
```

## Resources
- [ESLint Custom Rules](https://eslint.org/docs/developer-guide/working-with-rules)
- [OPA Policy Language](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [Pre-commit Framework](https://pre-commit.com/)

## Next Steps
For architecture blueprints, see `supabase-architecture-variants`.