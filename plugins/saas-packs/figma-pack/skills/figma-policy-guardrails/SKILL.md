---
name: figma-policy-guardrails
description: |
  Enforce security policies and coding standards for Figma API integrations.
  Use when setting up linting rules for Figma tokens, preventing accidental
  credential leaks, or enforcing API usage best practices.
  Trigger with phrases like "figma policy", "figma lint",
  "figma guardrails", "figma security rules", "figma best practices check".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Policy & Guardrails

## Overview
Automated guardrails for Figma API integrations: prevent token leaks, enforce scope minimization, validate webhook configurations, and catch common anti-patterns in CI.

## Prerequisites
- ESLint or similar linter
- CI/CD pipeline (GitHub Actions)
- Pre-commit hooks infrastructure

## Instructions

### Step 1: Token Leak Prevention
```bash
# .pre-commit-config.yaml -- catch Figma tokens before commit
repos:
  - repo: local
    hooks:
      - id: no-figma-tokens
        name: Check for Figma PAT leaks
        entry: bash -c '
          if git diff --cached --diff-filter=ACM -z -- . |
             xargs -0 grep -lP "figd_[a-zA-Z0-9_-]{20,}" 2>/dev/null; then
            echo "ERROR: Figma PAT found in staged files"
            echo "Store tokens in .env files (which should be in .gitignore)"
            exit 1
          fi
        '
        language: system
        pass_filenames: false
```

```yaml
# GitHub Actions secret scanning
# .github/workflows/figma-security.yml
name: Figma Security Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for Figma tokens
        run: |
          if grep -rP "figd_[a-zA-Z0-9_-]{20,}" \
            --include="*.ts" --include="*.js" --include="*.json" \
            --exclude-dir=node_modules .; then
            echo "::error::Figma PAT found in source code"
            exit 1
          fi

      - name: Check .env files not committed
        run: |
          if git ls-files --cached | grep -E '^\.(env|env\.local|env\.production)$'; then
            echo "::error::.env file committed to repository"
            exit 1
          fi
```

### Step 2: ESLint Rules for Figma
```javascript
// eslint-rules/no-figma-token-literal.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow hardcoded Figma PATs' },
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value === 'string' && /^figd_[a-zA-Z0-9_-]{20,}/.test(node.value)) {
          context.report({
            node,
            message: 'Hardcoded Figma PAT detected. Use process.env.FIGMA_PAT instead.',
          });
        }
      },
      TemplateLiteral(node) {
        for (const quasi of node.quasis) {
          if (/figd_[a-zA-Z0-9_-]{20,}/.test(quasi.value.raw)) {
            context.report({
              node,
              message: 'Hardcoded Figma PAT in template literal.',
            });
          }
        }
      },
    };
  },
};
```

### Step 3: API Usage Policies
```typescript
// Runtime guardrails for Figma API usage

// Policy 1: No full-file fetches without justification
function validateFigmaRequest(path: string) {
  // Block unoptimized full file fetches
  if (path.match(/\/v1\/files\/[^/]+$/) && !path.includes('depth=')) {
    console.warn(
      '[figma-policy] Full file fetch without depth parameter. ' +
      'Use ?depth=1 or /nodes endpoint for better performance.'
    );
  }

  // Block deprecated scope indicator
  if (path.includes('files:read')) {
    throw new Error(
      '[figma-policy] files:read scope is deprecated. ' +
      'Use file_content:read instead.'
    );
  }
}

// Policy 2: Enforce timeout on all Figma calls
function validateTimeout(options: RequestInit) {
  if (!options.signal) {
    console.warn(
      '[figma-policy] Figma request without AbortSignal. ' +
      'Use AbortSignal.timeout() to prevent hung requests.'
    );
  }
}

// Policy 3: Rate limit safety margin
const MAX_REQUESTS_PER_MINUTE = 25; // Conservative limit
let requestsThisMinute = 0;
let minuteStart = Date.now();

function enforceRatePolicy() {
  if (Date.now() - minuteStart > 60_000) {
    requestsThisMinute = 0;
    minuteStart = Date.now();
  }

  requestsThisMinute++;
  if (requestsThisMinute > MAX_REQUESTS_PER_MINUTE) {
    throw new Error(
      `[figma-policy] Rate limit safety: ${requestsThisMinute} requests/min ` +
      `exceeds policy limit of ${MAX_REQUESTS_PER_MINUTE}`
    );
  }
}
```

### Step 4: Configuration Validation
```typescript
// Validate Figma config at startup, fail fast if misconfigured
function validateFigmaConfig() {
  const errors: string[] = [];

  // Token format
  const pat = process.env.FIGMA_PAT;
  if (!pat) {
    errors.push('FIGMA_PAT is not set');
  } else if (!pat.startsWith('figd_')) {
    errors.push('FIGMA_PAT does not have expected figd_ prefix');
  }

  // File key format
  const fileKey = process.env.FIGMA_FILE_KEY;
  if (!fileKey) {
    errors.push('FIGMA_FILE_KEY is not set');
  } else if (fileKey.length < 10) {
    errors.push('FIGMA_FILE_KEY seems too short');
  }

  // Webhook passcode (if webhooks are configured)
  if (process.env.FIGMA_WEBHOOK_ENABLED === 'true') {
    if (!process.env.FIGMA_WEBHOOK_PASSCODE) {
      errors.push('FIGMA_WEBHOOK_PASSCODE required when webhooks are enabled');
    } else if (process.env.FIGMA_WEBHOOK_PASSCODE.length < 16) {
      errors.push('FIGMA_WEBHOOK_PASSCODE should be at least 16 characters');
    }
  }

  if (errors.length > 0) {
    console.error('[figma-policy] Configuration errors:');
    errors.forEach(e => console.error(`  - ${e}`));
    throw new Error(`Figma configuration invalid: ${errors.length} errors`);
  }

  console.log('[figma-policy] Configuration validated');
}

// Call at startup
validateFigmaConfig();
```

### Step 5: Audit Logging
```typescript
// Log all Figma API operations for compliance
interface FigmaAuditEntry {
  timestamp: string;
  action: string;
  endpoint: string;
  fileKey?: string;
  status: number;
  userId?: string;
}

function auditFigmaCall(entry: Omit<FigmaAuditEntry, 'timestamp'>) {
  const log: FigmaAuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };

  // Structured log for aggregation
  console.log(JSON.stringify({ type: 'figma_audit', ...log }));
}
```

## Output
- Pre-commit hooks catching token leaks
- CI pipeline scanning for hardcoded credentials
- Runtime policies enforcing performance best practices
- Configuration validation at startup
- Audit logging for compliance

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| False positive on token scan | Test fixture contains figd_ | Exclude test fixtures directory |
| Policy blocks legitimate request | Too restrictive | Add exception list for specific paths |
| Startup validation fails | Missing env vars | Check deployment config |
| Audit log noise | Too many entries | Filter to write operations only |

## Resources
- [Figma API Scopes](https://developers.figma.com/docs/rest-api/scopes/)
- [Pre-commit Framework](https://pre-commit.com/)
- [ESLint Custom Rules](https://eslint.org/docs/latest/extend/custom-rules)

## Next Steps
For architecture blueprints, see `figma-architecture-variants`.
