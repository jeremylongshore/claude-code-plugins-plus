---
name: supabase-policy-guardrails
description: |
  Implement Supabase guardrails: ESLint rules for Supabase anti-patterns,
  pre-commit hooks blocking secrets, CI policy checks for RLS,
  and runtime safety guards for production.
  Trigger with phrases like "supabase policy", "supabase lint",
  "supabase guardrails", "supabase eslint", "supabase pre-commit".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, code-quality, guardrails]

---
# Supabase Policy Guardrails

## Overview
Defense-in-depth guardrails for Supabase: lint rules catching anti-patterns at code time, pre-commit hooks preventing secret leaks, CI checks enforcing RLS, and runtime guards preventing accidental destructive operations.

## Prerequisites
- ESLint configured in project
- Husky or similar pre-commit hook tool
- CI/CD pipeline (GitHub Actions)
- TypeScript for type enforcement

## Instructions

### Guardrail 1: ESLint Rules for Supabase

```javascript
// eslint-rules/no-select-star.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow .select("*") in Supabase queries' },
    messages: {
      noSelectStar: 'Specify column names instead of select("*") to reduce bandwidth and prevent leaking sensitive columns.',
    },
  },
  create(context) {
    return {
      CallExpression(node) {
        if (
          node.callee.property?.name === 'select' &&
          node.arguments[0]?.value === '*'
        ) {
          context.report({ node, messageId: 'noSelectStar' })
        }
      },
    }
  },
}

// eslint-rules/no-service-key-client.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Prevent service role key in client-side code' },
    messages: {
      serviceKeyInClient: 'SUPABASE_SERVICE_ROLE_KEY must not be used in client-side code. Use SUPABASE_ANON_KEY instead.',
    },
  },
  create(context) {
    const filename = context.getFilename()
    const isClientSide = filename.includes('/src/') ||
                          filename.includes('/components/') ||
                          filename.includes('/pages/') ||
                          filename.includes('/app/')

    return {
      MemberExpression(node) {
        if (isClientSide && node.property?.name === 'SUPABASE_SERVICE_ROLE_KEY') {
          context.report({ node, messageId: 'serviceKeyInClient' })
        }
      },
      Literal(node) {
        if (isClientSide && typeof node.value === 'string' &&
            node.value.includes('SERVICE_ROLE_KEY')) {
          context.report({ node, messageId: 'serviceKeyInClient' })
        }
      },
    }
  },
}
```

```javascript
// .eslintrc.js — register the rules
module.exports = {
  rules: {
    'supabase/no-select-star': 'error',
    'supabase/no-service-key-client': 'error',
  },
  plugins: ['supabase'],
}
```

### Guardrail 2: Pre-Commit Hook for Secrets

```bash
# Install husky
npx husky install

# Add pre-commit hook
npx husky add .husky/pre-commit 'bash scripts/check-secrets.sh'
```

```bash
#!/bin/bash
# scripts/check-secrets.sh
set -euo pipefail

echo "Checking for Supabase secrets in staged files..."

# Pattern: Supabase keys start with eyJ (base64 JWT)
# Exclude .env files, test fixtures, and lock files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | \
  grep -v '.env' | grep -v 'package-lock.json' | grep -v 'pnpm-lock.yaml' || true)

if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

# Check for JWT-like strings (Supabase keys)
if echo "$STAGED_FILES" | xargs grep -lE 'eyJ[A-Za-z0-9_-]{50,}\.' 2>/dev/null; then
  echo ""
  echo "ERROR: Possible Supabase API key found in staged files."
  echo "Use environment variables instead of hardcoded keys."
  echo "If this is a false positive, use git commit --no-verify"
  exit 1
fi

# Check for Supabase connection strings
if echo "$STAGED_FILES" | xargs grep -lE 'postgres://postgres\.[a-z]+:' 2>/dev/null; then
  echo ""
  echo "ERROR: Supabase connection string found in staged files."
  echo "Use DATABASE_URL environment variable instead."
  exit 1
fi

echo "No secrets detected."
```

### Guardrail 3: CI RLS Policy Check

```yaml
# .github/workflows/supabase-guardrails.yml
name: Supabase Guardrails

on: [pull_request]

jobs:
  check-rls:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1

      - name: Start local Supabase
        run: supabase start

      - name: Apply migrations
        run: supabase db reset

      - name: Check RLS enabled on all tables
        run: |
          MISSING_RLS=$(supabase db query "
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND rowsecurity = false
            AND tablename NOT LIKE '\_%'
          " --output csv | tail -n +2)

          if [ -n "$MISSING_RLS" ]; then
            echo "::error::Tables missing RLS: $MISSING_RLS"
            exit 1
          fi
          echo "All public tables have RLS enabled"

      - name: Check no destructive migrations without annotation
        run: |
          for file in supabase/migrations/*.sql; do
            if grep -qi 'DROP TABLE\|TRUNCATE\|DELETE FROM.*WHERE.*true' "$file"; then
              if ! grep -qi '-- APPROVED-DESTRUCTIVE' "$file"; then
                echo "::error::Destructive operation in $file without -- APPROVED-DESTRUCTIVE annotation"
                exit 1
              fi
            fi
          done
          echo "Migration safety check passed"

      - name: Stop Supabase
        if: always()
        run: supabase stop
```

### Guardrail 4: Runtime Safety Guards

```typescript
// lib/safety-guards.ts
import { getEnvironment } from './config'

export function guardBulkDelete(table: string, filter: Record<string, any>) {
  if (getEnvironment() === 'production') {
    const filterKeys = Object.keys(filter)
    if (filterKeys.length === 0) {
      throw new Error(`[SAFETY] Bulk delete on ${table} without filters blocked in production`)
    }
  }
}

export function guardServiceKeyUsage(context: string) {
  if (typeof window !== 'undefined') {
    throw new Error(`[SAFETY] Service role key used in browser context: ${context}`)
  }
}

// Usage in service layer
async function deleteCompletedTodos(userId: string) {
  guardBulkDelete('todos', { user_id: userId, is_complete: true })

  const { error } = await supabase
    .from('todos')
    .delete()
    .eq('user_id', userId)
    .eq('is_complete', true)

  if (error) throw error
}
```

### Guardrail 5: Migration Naming Convention Check

```bash
#!/bin/bash
# scripts/check-migration-names.sh
# Enforce naming: <timestamp>_<verb>_<description>.sql

for file in supabase/migrations/*.sql; do
  basename=$(basename "$file")
  if ! echo "$basename" | grep -qE '^[0-9]{14}_(create|alter|drop|add|remove|update|fix|seed)_[a-z_]+\.sql$'; then
    echo "ERROR: Migration '$basename' doesn't match naming convention"
    echo "Expected: <timestamp>_<verb>_<description>.sql"
    echo "Example: 20240101000000_create_users_table.sql"
    exit 1
  fi
done

echo "All migration names follow convention."
```

## Output
- ESLint rules catching `select("*")` and service key in client code
- Pre-commit hooks blocking hardcoded Supabase secrets
- CI check verifying RLS on all tables and safe migrations
- Runtime guards blocking bulk deletes and browser service key usage
- Migration naming convention enforcement

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| ESLint rule false positive | Legitimate `select('*')` needed | Use `// eslint-disable-next-line` with explanation |
| Pre-commit blocks test data | Test fixture contains JWT-like strings | Add test file to exclusion pattern |
| CI RLS check fails | New table missing RLS | Add `alter table ... enable row level security` to migration |

## Resources
- [ESLint Custom Rules](https://eslint.org/docs/latest/extend/plugins)
- [Husky](https://typicode.github.io/husky/)
- [Supabase Security Guide](https://supabase.com/docs/guides/security)

## Next Steps
For architecture variants, see `supabase-architecture-variants`.
