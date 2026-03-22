---
name: canva-policy-guardrails
description: |
  Implement Canva Connect API lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Canva integrations, implementing
  pre-commit hooks, or configuring CI policy checks.
  Trigger with phrases like "canva policy", "canva lint",
  "canva guardrails", "canva best practices check", "canva eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Policy & Guardrails

## Overview

Automated policy enforcement for Canva Connect API integrations — prevent token leaks, enforce rate limit handling, require error handling, and validate OAuth configuration.

## ESLint Rules

### No Hardcoded Credentials

```javascript
// eslint-rules/no-canva-credentials.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow hardcoded Canva OAuth credentials' },
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value !== 'string') return;
        const val = node.value;

        // Canva client IDs start with "OCA"
        if (/^OCA[A-Za-z0-9]{10,}/.test(val)) {
          context.report({ node, message: 'Hardcoded Canva client ID detected. Use environment variable.' });
        }

        // Canva access tokens start with "cnvat_"
        if (/^cnvat_[A-Za-z0-9]{20,}/.test(val)) {
          context.report({ node, message: 'Hardcoded Canva access token detected. Use environment variable.' });
        }
      },
    };
  },
};
```

### Require Rate Limit Handling

```javascript
// eslint-rules/require-canva-retry.js
module.exports = {
  meta: {
    type: 'suggestion',
    docs: { description: 'Canva API calls should handle 429 responses' },
  },
  create(context) {
    return {
      CallExpression(node) {
        // Check for fetch calls to api.canva.com
        if (node.callee.name === 'fetch' &&
            node.arguments[0]?.value?.includes('api.canva.com')) {
          // Check if parent is try-catch or has .catch()
          const parent = node.parent;
          if (parent.type !== 'AwaitExpression' ||
              parent.parent?.type !== 'TryStatement') {
            context.report({
              node,
              message: 'Canva API calls should be wrapped in try-catch with 429 handling',
            });
          }
        }
      },
    };
  },
};
```

## Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: canva-no-tokens
        name: Check for Canva tokens
        entry: bash -c 'git diff --cached --name-only | xargs grep -lE "(cnvat_|OCA[A-Z0-9]{10})" 2>/dev/null && echo "ERROR: Canva credentials found" && exit 1 || exit 0'
        language: system
        pass_filenames: false

      - id: canva-no-raw-urls
        name: Check for hardcoded Canva API URLs
        entry: bash -c 'git diff --cached --name-only | xargs grep -lE "api\.canva\.com/rest/v1" --include="*.ts" --include="*.js" 2>/dev/null | while read f; do grep -n "api\.canva\.com" "$f" | grep -v "const.*BASE\|const.*URL\|import\|from\|//" && echo "WARNING: Direct Canva URL in $f — use client wrapper" && exit 1; done; exit 0'
        language: system
        pass_filenames: false
```

## CI Policy Checks

```yaml
# .github/workflows/canva-policy.yml
name: Canva Policy Check

on: [push, pull_request]

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for hardcoded credentials
        run: |
          if grep -rE "(cnvat_[a-zA-Z0-9]{20,}|OCA[A-Z0-9]{10,})" \
            --include="*.ts" --include="*.js" --include="*.json" \
            --exclude-dir=node_modules .; then
            echo "ERROR: Hardcoded Canva credentials found"
            exit 1
          fi

      - name: Check for unhandled API calls
        run: |
          # Warn if raw fetch to Canva without error handling
          DIRECT_CALLS=$(grep -rn "fetch.*api\.canva\.com" \
            --include="*.ts" --include="*.js" \
            --exclude="*client.ts" --exclude="*test*" \
            . 2>/dev/null | wc -l)
          if [ "$DIRECT_CALLS" -gt 0 ]; then
            echo "WARNING: $DIRECT_CALLS direct Canva API calls found outside client wrapper"
            grep -rn "fetch.*api\.canva\.com" --include="*.ts" --include="*.js" \
              --exclude="*client.ts" --exclude="*test*" .
          fi

      - name: Validate .env.example
        run: |
          if [ -f .env.example ]; then
            for var in CANVA_CLIENT_ID CANVA_CLIENT_SECRET CANVA_REDIRECT_URI; do
              if ! grep -q "^${var}=" .env.example; then
                echo "WARNING: ${var} missing from .env.example"
              fi
            done
          fi
```

## Runtime Guardrails

```typescript
// Prevent dangerous operations and enforce patterns at runtime

class CanvaGuardrails {
  // Block requests without proper authorization header
  static validateRequest(init: RequestInit): void {
    const authHeader = (init.headers as Record<string, string>)?.['Authorization'];
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new Error('Canva API call missing Bearer token');
    }
  }

  // Enforce token is not expired before making call
  static validateToken(expiresAt: number): void {
    if (Date.now() > expiresAt) {
      throw new Error('Canva access token expired — refresh before calling');
    }
  }

  // Block sensitive operations based on environment
  static validateEnvironment(operation: string): void {
    const blocked = ['deleteAsset', 'deleteFolder'];
    if (process.env.NODE_ENV !== 'production' && blocked.includes(operation)) {
      // Allow in dev for testing
      return;
    }
    // In production, require explicit confirmation
    if (process.env.NODE_ENV === 'production' && blocked.includes(operation)) {
      console.warn(`[guardrail] Destructive operation: ${operation}`);
    }
  }

  // Rate limit self-check — don't send if we know we'll get 429
  static checkRateLimit(
    endpoint: string,
    tracker: Map<string, { count: number; resetAt: number }>
  ): void {
    const window = tracker.get(endpoint);
    if (window && window.count <= 0 && Date.now() < window.resetAt) {
      const waitMs = window.resetAt - Date.now();
      throw new Error(`Rate limit exhausted for ${endpoint}. Wait ${(waitMs / 1000).toFixed(0)}s`);
    }
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| ESLint rule not firing | Wrong config path | Check plugin registration |
| Pre-commit skipped | `--no-verify` used | Enforce in CI |
| False positive on "OCA" | String matches pattern | Narrow regex or add allowlist |
| Guardrail blocks valid op | Too strict | Add environment-based exceptions |

## Resources

- [ESLint Plugin Development](https://eslint.org/docs/latest/extend/plugins)
- [Pre-commit Framework](https://pre-commit.com/)
- [Canva Scopes](https://www.canva.dev/docs/connect/appendix/scopes/)

## Next Steps

For architecture blueprints, see `canva-architecture-variants`.
